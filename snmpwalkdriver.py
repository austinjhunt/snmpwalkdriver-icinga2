""" Module used by Icinga2 for executing snmpwalk checks and 
applying logic to the check outputs to determine check status """

import argparse, sys, subprocess, requests,json,urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

NETBOX_API_TOKEN = "CHANGEME-NETBOX-API-TOKEN"
# Default: Juniper = 2636, this number is part of OID, will 
# be used to split OID to get part after it in order to count 
# active members of virtual chassis
DEVICE_MANUFACTURER_NUMBER = "2636" 

# API Token generated on Nov 6, 2020
def get_member_count(api_url):
    # This token was pulled from the already-in-use api calls from icinga2 director to Netbox
    headers = {"Authorization": f"Token {NETBOX_API_TOKEN}"}
    try:
        response = requests.get(api_url, headers=headers,verify=False)
        body = response.json()
        print(body)
        member_count = body['member_count']
        print(f"Based on Netbox, the expected member count is {member_count}")
        return member_count
    except Exception as e:
        print(e)
        sys.exit(3)

# Sample command call looks like:
# snmpwalk -v VERSION -X PRIVPASS -A AUTHPASS -a AUTHPROTOCOL -x PRIVPROTOCOL -l SECURITYLEVEL -u USER HOSTIP OID
# When script called
if __name__ == "__main__":
    # Initialize arguments
    SNMP_VERSION = 3
    SNMP_PRIV_PASS = ""
    SNMP_AUTH_PASS = ""
    SNMP_AUTH_PROTO = ""
    SNMP_PRIV_PROTO = ""
    SNMP_SEC_LEVEL = ""
    SNMP_USER = ""
    SNMP_HOST_ADDRESS = ""
    SNMP_OID = ""
    SNMP_EXPECTED_NUM_MEMBERS = 2
    VIRTUAL_CHASSIS_URL = ""

    # What is being checked? 
    SNMP_CHECK_TYPE = ""

    parser = argparse.ArgumentParser()

    parser = argparse.ArgumentParser(description='Get arguments from NotificationCommand object.')
    parser.add_argument("-v", help="snmp version", type=str, default="")
    parser.add_argument("-X", help="privacy protocol passphrase", type=str, default="")
    parser.add_argument("-A", help="authentication protocol passphrase", type=str, default="")
    parser.add_argument("-a", help="authentication protocol", type=str, default="SHA")
    parser.add_argument("-x", help="privacy protocol", type=str, default="DES")
    parser.add_argument("-l", help="security level", type=str, default="authPriv")
    parser.add_argument("-u", help="username", type=str, default="")
    parser.add_argument("hostaddress", help="address", type=str)
    parser.add_argument("oid", help="address", type=str, default="1.3.6.1.4.1.2636.3.40.1.4.1.1.1.7") # uptime is default
    parser.add_argument("--expected_num_members", help="expected num members in VC", type=str, default="2")
    parser.add_argument("--virtual_chassis_url", help="API url of virtual chassis to get expected member count")
    parser.add_argument("--snmp_check_type", help="What is being checked with this service check? Will determine how snmpwalk output is parsed")
    args = parser.parse_args()
    try:
        SNMP_VERSION = args.v
        SNMP_PRIV_PASS = args.X
        SNMP_AUTH_PASS = args.A
        SNMP_PRIV_PROTO = args.x
        SNMP_AUTH_PROTO = args.a
        SNMP_SEC_LEVEL = args.l
        SNMP_USER = args.u
        SNMP_HOST_ADDRESS = args.hostaddress
        SNMP_OID = args.oid
        SNMP_CHECK_TYPE = args.snmp_check_type

        # if the check type == "virtual-chassis-netbox-compare", this variable will be used
        VIRTUAL_CHASSIS_URL = args.virtual_chassis_url
    

    except Exception as e:
        print(e)
        sys.exit(3)

    # Call the SNMP walk command and parse the output.
    out = subprocess.Popen([
        'snmpwalk','-v',SNMP_VERSION,'-X',SNMP_PRIV_PASS,'-A',SNMP_AUTH_PASS,
        '-x', SNMP_PRIV_PROTO, '-a', SNMP_AUTH_PROTO, '-l', SNMP_SEC_LEVEL,
        '-u', SNMP_USER, SNMP_HOST_ADDRESS, SNMP_OID
    ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout, stderr = out.communicate()

    if stdout is not None:
        # If this is a virtual chassis check to be compared with an expected number of members from Netbox API URL
        if SNMP_CHECK_TYPE == "virtual-chassis-netbox-compare" and VIRTUAL_CHASSIS_URL: 
            # Then use that URL to get the expected number of members.
            SNMP_EXPECTED_NUM_MEMBERS = get_member_count(VIRTUAL_CHASSIS_URL)
            print(stdout.decode('ascii'))
            # num_lines = len(str(stdout).split("\r"))
            # get the part of the oid starting at
            last_part_of_oid = SNMP_OID.split(DEVICE_MANUFACTURER_NUMBER)[-1]
            num_lines = str(stdout).count(last_part_of_oid)

            # FIXME: just temporary; needs to be ==, but need dynamic variable for expected num members
            # to be pulled from netbox in order for that not to throw an error.
            e = 0
            if num_lines >= SNMP_EXPECTED_NUM_MEMBERS:
                print("All members of virtual chassis are up!")
                # e already 0
            elif num_lines < SNMP_EXPECTED_NUM_MEMBERS and num_lines > 0:
                print(f"There are only {num_lines} members up :(")
                e = 1
            elif num_lines == 0:
                print("Virtual Chassis is down")
                e = 2
            # Performance Data for Graphing inline.
            print(f"| active_vc_members={num_lines}")
            sys.exit(e)
        elif SNMP_CHECK_TYPE and "alarm-count" in SNMP_CHECK_TYPE:
            # Print the SNMPWalk output 
            print(stdout.decode('ascii'))

            # this will be either a juniper-red-alarm-count or juniper-yellow-alarm-count service check
            # The count will be the last value in the stdout.decode('ascii') output.
            # initialize exit status to 0 (good)
            exit_status = 0 
            count = 0
            try:  
                count = int(stdout.decode('ascii').strip().split()[-1])
                if "red" in SNMP_CHECK_TYPE and count > 0: 
                    # Checking the red alarm. Throw critical if count > 0, no warnings for red, just critical. 
                    exit_status = 2
                elif "yellow" in SNMP_CHECK_TYPE and count > 0: 
                    # If yellow count > 0 throw warning (exit 1). No criticals for yellow alarm check.
                    exit_status = 1
            except ValueError as e: 
                print(e)
                exit_status = 3 
            except Exception as e: 
                print(e)
                exit_status = 3 
            # Want to be able to monitor the alarm_count. No need to label red_alarm_count and yellow_alarm_count
            # because red and yellow are distinct service checks in Icinga2. Each will have its own alarm_count graph. 
            print(f"| alarm_count={count}")
            sys.exit(exit_status) 
            

    if stderr is not None:
        print(stderr)
        sys.exit(3) 
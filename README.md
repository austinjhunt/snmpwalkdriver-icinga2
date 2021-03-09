# Icinga2 Plugin - SNMP Walk Driver
This is a Python module wrapping the `snmpwalk` command and offering the ability to use Python to:
* execute snmp checks against networked hosts
* execute logic on the output of those checks

This module is specifically designed to be used with Icinga2. It currently supports two primary check methods: 
*  Virtual Chassis Check
   *  This check works as follows:
      *  First, it uses a given host's virtual chassis url (passed as `--virtual_chassis_url` to the script) to get the expected member count for the virtual chassis. This URL comes from the `virtual_chassis__url` property of a given host returned by the `/api/dcim/devices/` Netbox REST API endpoint. 
      *  Then, it runs an `snmpwalk` command to get the real active member count of the virtual chassis. 
      *  It runs a comparison between the expected count (from Netbox) and the real active count (from `snmpwalk`) and generates the appropriate exit status based on the comparison result. 
         *  If real active count >= expected count, exit status = 0 (OK)
         *  If real active count > 0 and < expected count, exit status = 1 (WARNING)
         *  If real active count == 0, all members down, exit status = 2 (CRITICAL)
      *  It prints data for time series graphing as `print(f"|active_vc_members={num_lines}")` to record the member count over time, where `num_lines` is the real active count from the `snmpwalk` 
      *  It exits with generated exit status from comparison. 
   *  Alarm count (count red or yellow alarms)
      *  For red alarms, it counts the number of results in the `snmpwalk` output that counts the red alarms and sets exit status = 2 (CRITICAL) if the count is greater than 0 (one or more red alarms is critical)
      *  For yellow alarms, it counts the number of results in the `snmpwalk` output that counts the yellow alarms and sets exit status = 1 (WARNING) if the count is greater than 0 (one or more yellow alarms is a warning)
      *  It prints data for time series graphing as `print(f"| alarm_count={count}")` to record the alarm count for a given service check over time, and exits with the generated exit status. 
---
## Usage
To use this with your Icinga2 instance, you will need to: 
1. Have a functional Netbox instance.
   1. If you have this, generate an API token to be used by this script or share a token already used by another script/application.
2. Have a functional Icinga2 instance, preferably with Icinga Director. 
3. In Icinga Director, create the following data fields: 
   1. virtual_chassis_url
   2. snmp_check_type 
   3. snmpv3_oid   
   4. snmp_version  
4.  In Icinga Director, create a Service Template and add those data fields above to the template. Alternatively, add those data fields to an existing Service Template you are already using. 
5.  Create an Import Source and Sync Rule that will synchronize Icinga2 hosts with Netbox using the Netbox API. Use [this open source project from digitalocean](https://github.com/digitalocean/icingaweb2-module-netboximport) to achieve this.
6.  For your sync rule, add the Virtual Chassis URL property highlighted in red in the following image: 
![sync rule ](https://github.com/austinjhunt/snmpwalkdriver-icinga2/blob/main/images/screenshot1.png?raw=true)
7.  Open Icinga Director > Commands, and add a new command. 
    1.  Call it virtual-chassis-snmp-command, and give it the absolute path to the `snmpwalkdriver.py` script that you want to execute. 
    2.  Open the `Arguments` tab for the command you are creating.
    3.  Add the following arguments/values, replacing the red text with your own values that you use for SNMP checks against your hosts: 
![sync rule ](https://github.com/austinjhunt/snmpwalkdriver-icinga2/blob/main/images/screenshot2.png?raw=true)
8. Open `Icinga Director > Services > Service Apply Rules`
   1. Create a new service apply rule
   2. Import the template to which you added the SNMP fields above. You will specify values for these fields for this specific Service Apply Rule.
   3. Set your "Assign where" option based on the hosts you want to execute virtual chassis checks against
   4. For the `virtual_chassis_url` field, set the value to `$host.vars.virtual_chassis_url$` which will use the value pulled from the Netbox API Sync Rule. 
   5. For the `snmp_check_type` field, use `virtual-chassis-netbox-compare`
   6. For the `snmp_version` field, use `3`
   7. For the `snmpv3_oid` field, use the OID that is used to check virtual chassis members for your device(s). 
   8. Save the service apply rule. 
9. Open `Icinga Director > Deployments > Render Config > Deploy`
   
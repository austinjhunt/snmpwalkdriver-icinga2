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
   1. snmpv3_auth_alg
   2. snmpv3_seclevel
   3. virtual_chassis_url
   4. snmp_check_type
   5. snmpv3_address
   6. snmpv3_auth_key
   7. snmpv3_oid
   8. snmpv3_priv_key
   9. snmpv3_user
   10. snmp_crit
   11. snmp_version
   12. snmp_warn
   13. snmp_oid
4.  In Icinga Director, create a Service Template and add those data fields above to the template. Alternatively, add those data fields to an existing Service Template you are already using. 
5.  Create an Import Source and Sync Rule that will synchronize Icinga2 hosts with Netbox using the Netbox API. Use [this open source project from digitalocean](https://github.com/digitalocean/icingaweb2-module-netboximport) to achieve this.
6.  For your sync rule, add the Virtual Chassis URL property highlighted in red in the following image: 
    1.  ![sync rule ](https://github.com/austinjhunt/snmpwalkdriver-icinga2/blob/main/images/screenshot1.png?raw=true)
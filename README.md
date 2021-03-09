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



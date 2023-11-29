# TODO for Home Energy Hub Addon

## Global Tasks
- **Code Structure (Top Priority):**
  - Rethink the layout of global variables for improved clarity, using the format `hass[DOMAIN][ENTRY_ID][SERVICE/DEVICE][ENTRY]`.
  - Assess and refine the wait function, specifically `CheckLastRun(UID, Time Setting)`.
  - Investigate the feasibility of setting coordinator update times at specific intervals, such as every 30 minutes for Agile Tariffs or midnight for others.
      ~~~
      from datetime import datetime, timedelta
      
      # Assuming you have a coordinator instance like this
      coordinator = ...
      
      # Set the desired update interval (e.g., every 30 minutes)
      update_interval = timedelta(minutes=30)
      
      # Calculate the initial delay until the next 30-minute boundary
      now = datetime.now()
      current_minute = now.minute
      remaining_minutes = 30 - (current_minute % 30)
      initial_delay = timedelta(minutes=remaining_minutes)
      
      # Set the start time and interval
      coordinator.update_interval = update_interval
      coordinator.start_time = now + initial_delay
      ~~~
      
      ~~~
      from datetime import datetime, timedelta
      
      # Assuming you have a coordinator instance like this
      coordinator = ...
      
      # Set the desired update interval (e.g., every 30 minutes)
      update_interval = timedelta(minutes=30)
      
      # Calculate the initial delay until midnight
      now = datetime.now()
      midnight = datetime(now.year, now.month, now.day, 0, 0, 0)
      initial_delay = midnight - now
      
      # Set the start time and interval
      coordinator.update_interval = update_interval
      coordinator.start_time = now + initial_delay
      
      ~~~
  - Conduct a comprehensive review of existing modules, focusing on enhancing code structure by breaking it into functions.
  - Enhance debug logging for selective per-module enable/disable functionality and robust error handling.

## Config Flows
- Implement validation checks.
- Improve the handling of multiple entries for the same service, ensuring that adding multiple "helper services" creates distinct services under a single entry.
     ~~~
      class Entry:
          def __init__(self, entry_id):
              self.entry_id = entry_id
              self.services = []
      
      def add_service_to_entry(entry_id, service):
          # Check if the entry already exists
          if entry_id in entries:
              # Add the service to the existing entry
              entries[entry_id].services.append(service)
          else:
              # Create a new entry and add the service to it
              new_entry = Entry(entry_id)
              new_entry.services.append(service)
              entries[entry_id] = new_entry
     ~~~
     
# Seplos V2 BMS
- Implement support for handling multiple battery addresses.
- Consider opening the COM port globally and maintaining its open state.
- Optimize data retrieval by segregating information, avoiding unnecessary spamming of four serial commands every 5 seconds. Focus on frequent updates for critical data like Telemetry and Teledata, while less critical settings, exceeding 100+, can be updated at more reasonable intervals, such as every minute.

# Seplos V3 BMS
- Reintegrate code from V3 BMS Connector.
- Review Temp sensor data handling to ensure accurate PIC extraction.
- Reevaluate the process of extracting the battery address from the response to guarantee correct battery pack identification.
- Implement support for multiple battery addresses, moving away from fixed strings.
- Conduct thorough testing to validate proper functionality.

# Octopus Energy
- Confirm that all tariff entries continue to update even in cases of stored data with a lost connection to the OE API.
- Rearrange sensors, placing the json sensor as the attribute on current_price for improved organization.

## Agile Tariff
- Import Home Energy Hub Day ahead forecast.

## Tracker 
- Enhance data update timings.

## Account Information
- Expand current sensors using recently added GraphQL functions.

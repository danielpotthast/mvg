# MVG

The `mvg` sensor will give you the departure time of the next bus, tram, subway, or train at the next station or stop in the Munich public transport network. Additional details such as the line number and destination are present in the attributes.

## Configuration

To enable this sensor, add the following lines to your `configuration.yaml` file:

```yaml
# Example configuration.yaml entry
sensor:
  - platform: mvg
    nextdeparture:
     - station: STATION_OR_STOP_NAME
```

### Configuration Variables
- `station` (string, required):<br>
  Name of the stop or station. Visit [the MVG live web site](https://www.mvg.de/meinhalt.html) to find valid names. Be aware, that not all data of interest might be available (i.e., bus departure-times in Haar).
- `destinations` (list, optional):<br>
  description: One or multiple final stop names, e.g., 'Feldmoching' or ['Feldmoching','Harthof']. This can be used to only consider a particular direction of travel.
- `lines` (list, optional):<br>
  description: One or more line numbers, e.g., 'U2' or ['U2','U8','N41'].
- `products` (list, optional):<br>
  One or more modes of transport (default: all 5 modes ['U-Bahn', 'Tram', 'Bus', 'S-Bahn', 'Nachteule'])
- `timeoffset` (integer, optional, default: 0):<br>
  Do not display departures leaving sooner than this number of minutes. Useful if you are a couple of minutes away from the stop.
- `number` (integer, optional, default: 1):<br>
  Store a list of departures in the attribute "departures". If you set this parameter to 3, the next three departures will be stored.
- `name` (string, optional):<br>
  You can customize the name of the sensor, which defaults to the station name.

## Examples

### Full configuration

The example below shows a full configuration with three sensors that showcase the various configuration options.

```yaml
# Example configuration.yaml entry
sensor:
  - platform: mvg
    nextdeparture:
     - station: Hauptbahnhof
       name: Hbf
       destinations: ['Messestadt Ost','Erding']
       products: ['S-Bahn','U-Bahn']
       timeoffset: 2
     - station: Sendlinger Tor
       lines: ['U2','U8']
       number: 5
     - station: Scheidplatz
       products: ['U-Bahn']
```

The first sensor will return S-Bahn and U-Bahn departures to Messestadt Ost or Erding that are at least 2 minutes away.
The second sensor returns U2 and U8 departures from Sendlinger Tor and stores a total of 5 departures in attributes. To retrieve the time until the second departure, you would use `state_attr('sensor.ENTITY_NAME', 'departures')[1].time_in_mins`.
The third sensor returns all U-Bahn trains from Scheidplatz.

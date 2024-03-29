> [!WARNING]
> This project is not an official project from the Münchner Verkehrsgesellschaft (MVG).
> Therefore, the following usage restrictions from the MVG Imprint do apply to all users of this home assistant integration:
>
> > Our systems are used for direct customer interaction. The processing of our content or data by third parties requires our express consent. For private, non-commercial purposes, moderate use is tolerated without our explicit consent. Any form of data mining does not constitute moderate use. We reserve the right to revoke this permission in principle or in individual cases. Please direct any questions to: redaktion@mvg.de<br>
> >
> > (from https://www.mvg.de/impressum.html, accessed on 13. Nov 2023)

# HACS-Plugin: MVG

The `mvg` sensor will give you the departure time of the next bus, tram, subway, or train at the next station or stop in the Munich public transport network. Additional details such as the line number and destination are present in the attributes.

## Credits

I've copied and adapted the code from [fellnerse](https://github.com/fellnerse)’s [PR](https://github.com/home-assistant/core/pull/97271).

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

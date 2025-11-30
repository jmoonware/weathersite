import requests
import settings

def update_forecast():
    forecast_string = 'None'
    forecast_string_1 = 'None'

    # Get the forecast string from National Weather Service
    forecast_url = settings.forecast_url
    r = None
    forecast_strings = []
    hazard_strings = []
    try:
        with requests.Session() as req:
            r = req.get(forecast_url)
        if r:
            lines=r.text.split('\n')
            fc = [l for l in lines if 'period-name' in l]
#            breakpoint()
            if len(fc) == 1:
                forecast_strings = [l.split('title=')[0].replace('"','').strip() for l in fc[0].split('alt=')[1:]]
            elif len(fc) == 2:
                forecast_strings = [l.split('title=')[0].replace('"','').strip() for l in fc[1].split('alt=')[1:]]
            else: # old format
                for l,nl in zip(lines[:-1],lines[1:]):
                    if 'period-name' in l:
                        fs = nl.split('title=')[1].split('class')[0].strip().replace('"','')
                        if len(fs) > 0:
                            forecast_strings.append(fs)
                    if "HAZARDOUS WEATHER CONDITIONS" in l.upper():
                        hws = l.split('class="anchor-hazards">')
                        for hwsi in hws:
                            toks=hwsi.split("<")
                            if len(toks) > 0 and len(toks[0]) > 0:
                                hazard_strings.append(toks[0].strip())
    

    except Exception as ex:
        print(ex)

    print(forecast_strings)
    print(hazard_strings)


update_forecast()

import pandas as pd
from datetime import date, datetime, timedelta
from urllib.error import HTTPError
import plotly.io as pio
import plotly.graph_objects as go

# constants to access csv data
DIMESSI = "dimessi_guariti"
NUOVI_POSITIVI = "nuovi_positivi"
DECEDUTI = "deceduti"
REGION_NAME = "denominazione_regione"
PROVINCE_NAME = "denominazione_provincia"
DATA = "data"
PROVINCE_TOTAL_CASES = "totale_casi"

# fix trentino sub region
TRENTINO_ALTO_ADIGE = "Trenitino-Alto Adige"
PA_BOLZANO = "P.A. Bolzano"
PA_TRENTO = "P.A. Trento"

# const for index name
TODAY = "today"
YESTERDAY = "yesterday"

# const for souce of data
SOURCE_PROTEZIONE_CIVILE = "Dati pubblicati dalla Protezione Civile\n" + \
                           "Link: https://github.com/pcm-dpc/COVID-19"


# TODO: create a method that retrive github document and remove duplicated code

def get_today_national_stats(params):
    """
    Retrive statistics about today and yesterday from Protezione Civile on github.
    Link: https://github.com/pcm-dpc/COVID-19
    :return: string for googleResponse textToSpeech and Facebook
    """
    country_org = params.get("location")  # original country used for response
    try:
        country_org = country_org.get("country")
    except AttributeError:
        pass  # if location is empty than we can assume it is Italy

    if country_org is not None:
        country = country_org.lower()
    else: country = "italia"

    if country != "italia" and country != "":
        return __country_not_found__(country, country_org), \
               __country_not_found__(country, country_org)  # This one is for facebook compatibility

    today = date.today().strftime("%Y%m%d")
    yesterday = date.strftime(datetime.now() - timedelta(1), "%Y%m%d")
    url_today = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita" \
                "-andamento-nazionale-{}.csv ".format(today)
    url_yesterday = url_today.replace(today, yesterday)

    try:  # look for today update release after 6:30 p.m.
        df_today = pd.read_csv(url_today, error_bad_lines=False)
    except HTTPError:  # if today update is not uploaded yet then look for the last update
        new_today = yesterday
        new_yesterday = date.strftime(datetime.now() - timedelta(2), "%Y%m%d")
        url_today = url_today.replace(today, new_today)
        url_yesterday = url_yesterday.replace(yesterday, new_yesterday)
        df_today = pd.read_csv(url_today, error_bad_lines=False)

    df_today.rename(index={0: TODAY}, inplace=True)
    df_yesterday = pd.read_csv(url_yesterday, error_bad_lines=False)
    df_yesterday.rename(index={0: YESTERDAY}, inplace=True)

    df_toRecap = df_today.append(df_yesterday)

    today_date = (df_today[DATA][0]).split("T")[0]

    return __make_today_national_stats_google_response__(df_toRecap, today_date), \
           __make__today_national_stats_facebook_response__(df_toRecap, today_date)


def __country_not_found__(countryName, originalName):
    displayText = "🧐Purtroppo non ho informazioni su{} ".format("lla" if countryName.endswith("a") else "l")

    displayText += originalName + ", attualmente riesco a darti informazioni sull'Italia " \
                                  "e le sue regioni"

    textToSpeech = displayText

    return textToSpeech, displayText


def get_today_regional_stats(params):
    region = params.get("region")
    today = date.today().strftime("%Y%m%d")
    yesterday = date.strftime(datetime.now() - timedelta(1), "%Y%m%d")

    url_today = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-regioni/" \
                "dpc-covid19-ita-regioni-{}.csv".format(today)
    url_yesterday = url_today.replace(today, yesterday)

    try:  # look for today update release after 6:30 p.m.
        df_today = pd.read_csv(url_today, error_bad_lines=False)
    except HTTPError:  # if today update is not uploaded yet then look for the last update
        new_today = yesterday
        new_yesterday = date.strftime(datetime.now() - timedelta(2), "%Y%m%d")
        url_today = url_today.replace(today, new_today)
        url_yesterday = url_yesterday.replace(yesterday, new_yesterday)
        df_today = pd.read_csv(url_today, error_bad_lines=False)

    today_date = (df_today[DATA][0]).split("T")[0]

    if (region == TRENTINO_ALTO_ADIGE):
        df_today = __trentinoFix__(df_today)
    else:
        df_today = df_today[df_today[REGION_NAME] == region]
    print(df_today)
    print(region)
    df_today.rename(index={df_today.index.values[0]: TODAY}, inplace=True)  # rename the index with today
    df_yesterday = pd.read_csv(url_yesterday, error_bad_lines=False)
    if (region == TRENTINO_ALTO_ADIGE):
        df_yesterday = __trentinoFix__(df_yesterday)
    else:
        df_yesterday = df_yesterday[df_yesterday[REGION_NAME] == region]
    df_yesterday.rename(index={df_yesterday.index.values[0]: YESTERDAY}, inplace=True)

    df_toRecap = df_today.append(df_yesterday)
    return __make__today_regional_stats_google_response__(df_toRecap, today_date), \
           __make__today_regional_stats_facebook_response__(df_toRecap, today_date)


def get_today_province_stats(params): # TODO: make it correct
    province = params.get("province")[0]
    today = date.today().strftime("%Y%m%d")
    yesterday = date.strftime(datetime.now() - timedelta(1), "%Y%m%d")

    url_today = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/" \
                "dati-province/dpc-covid19-ita-province-{}.csv".format(today)
    url_yesterday = url_today.replace(today, yesterday)

    try:  # look for today update release after 6:30 p.m.
        df_today = pd.read_csv(url_today, error_bad_lines=False)
    except HTTPError:  # if today update is not uploaded yet then look for the last update
        new_today = yesterday
        new_yesterday = date.strftime(datetime.now() - timedelta(2), "%Y%m%d")
        url_today = url_today.replace(today, new_today)
        url_yesterday = url_yesterday.replace(yesterday, new_yesterday)
        df_today = pd.read_csv(url_today, error_bad_lines=False)
    except UnicodeDecodeError:
        url_today = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/" \
                    "dati-province/dpc-covid19-ita-province-latest.csv"
        df_today = pd.read_csv(url_today, error_bad_lines=False)

    today_date = (df_today[DATA][0]).split("T")[0]
    print(PROVINCE_NAME)
    print(province)
    df_today = df_today[df_today[PROVINCE_NAME] == province]
    print(df_today[PROVINCE_NAME])
    #df_today.rename(index={df_today.index.values[0]: TODAY}, inplace=True)  # rename the index with today

    return __make_today_provincial_stats_google_response__(df_today, today_date), \
           __make_today__provincial_stats_google_response__(df_today, today_date)


def __make_today_provincial_stats_google_response__(data, date):
    print(data[PROVINCE_NAME].iloc[0])
    displayText = "A differenza delle regioni e della nazione, per le province sono disponibili" \
                  " il numero totale dei casi positivi.\n"
    displayText += "Situazione aggiornata della provincia {} al {}:\n".format(data[PROVINCE_NAME].iloc[0], date)

    displayText += "🔴 {} casi positivi totali \n".format(data[PROVINCE_TOTAL_CASES].iloc[0])

    displayText += SOURCE_PROTEZIONE_CIVILE
    displayText += "\n\n Posso esserti ancora d'aiuto?"

    textToSpeech = "A differenza delle regioni e della nazione, per le province sono disponibili" \
                  " il numero totale dei casi positivi.\n"
    textToSpeech += "Situazione aggiornata della provincia {} al {}:\n".format(data[PROVINCE_NAME].iloc[0], date)

    textToSpeech += "🔴 {} casi positivi totali \n".format(data[PROVINCE_TOTAL_CASES].iloc[0])

    textToSpeech += SOURCE_PROTEZIONE_CIVILE
    textToSpeech += "\n\n Posso esserti ancora d'aiuto?"

    return textToSpeech, displayText


def __make_today_national_stats_google_response__(data, date):
    today_vs_yesterday_positive = data[NUOVI_POSITIVI].loc[TODAY] - data[NUOVI_POSITIVI].loc[YESTERDAY]
    today_vs_yesterday_dead = data[DECEDUTI].loc[TODAY] - data[DECEDUTI].loc[YESTERDAY]
    today_vs_yesterday_healed = data[DIMESSI].loc[TODAY] - data[DIMESSI].loc[YESTERDAY]
    displayText = "Situazione aggiornata al {}:\n".format(date)

    displayText += "🔴 {} nuovi casi positivi;" \
        .format(data[NUOVI_POSITIVI].loc[TODAY], today_vs_yesterday_positive)

    displayText += "\n☠️ {} persone decedute, {} {} rispetto a ieri;" \
        .format(data[DECEDUTI].loc[TODAY], today_vs_yesterday_dead,
                " caso in più" if today_vs_yesterday_dead == 1 else "casi in più" if today_vs_yesterday_dead > 0 else "")

    displayText += "\n💚 {} dimessi dagli ospedali e guariti, {} {} rispetto a ieri." \
        .format(data[DIMESSI].loc[TODAY], today_vs_yesterday_healed,
                " caso in più" if today_vs_yesterday_healed == 1 else "casi in più" if today_vs_yesterday_healed > 0 else "")

    displayText += "\n"
    displayText += SOURCE_PROTEZIONE_CIVILE
    displayText += "\n\n Posso esserti ancora d'aiuto?"

    textToSpeech = "La situazione aggiornata è:\n"

    textToSpeech += "{} {} rispetto a ieri;" \
        .format(today_vs_yesterday_positive,
                " caso positivo in più" if today_vs_yesterday_positive == 1 else "casi positivi in più" if today_vs_yesterday_positive > 0 else "casi positivi")

    textToSpeech += "\n{} {} rispetto a ieri;" \
        .format(today_vs_yesterday_dead,
                " decesso in più" if today_vs_yesterday_dead == 1 else "decessi in più" if today_vs_yesterday_dead > 0 else "decessi")

    textToSpeech += "\n{} {} rispetto a ieri." \
        .format(today_vs_yesterday_healed,
                "dimesso dall'ospedale e guarito in più" if today_vs_yesterday_healed == 1 else "dimessi dall'ospedale e guariti in più" if today_vs_yesterday_healed > 0 else "dimessi e guariti")

    textToSpeech += "\n\n Posso esserti ancora d'aiuto?"

    return textToSpeech, displayText


def __make__today_regional_stats_google_response__(data, date):
    today_vs_yesterday_positive = data[NUOVI_POSITIVI].loc[TODAY] - data[NUOVI_POSITIVI].loc[YESTERDAY]
    today_vs_yesterday_dead = data[DECEDUTI].loc[TODAY] - data[DECEDUTI].loc[YESTERDAY]
    today_vs_yesterday_healed = data[DIMESSI].loc[TODAY] - data[DIMESSI].loc[YESTERDAY]
    # print(data)
    # data[REGION_NAME].loc[TODAY]
    displayText = "Situazione aggiornata al {}:\n".format(date)

    displayText += "🔴 {} nuovi casi positivi;" \
        .format(data[NUOVI_POSITIVI].loc[TODAY])

    displayText += "\n☠️ {} persone decedute, {} {} rispetto a ieri;" \
        .format(data[DECEDUTI].loc[TODAY], today_vs_yesterday_dead,
                " caso in più" if today_vs_yesterday_dead == 1 else "casi in più" if today_vs_yesterday_dead > 0 else "")

    displayText += "\n💚 {} dimessi dagli ospedali e guariti, {} {} rispetto a ieri." \
        .format(data[DIMESSI].loc[TODAY], today_vs_yesterday_healed,
                " caso in più" if today_vs_yesterday_healed == 1 else "casi in più" if today_vs_yesterday_healed > 0 else "")

    displayText += "\n" + SOURCE_PROTEZIONE_CIVILE
    displayText += "\n\nPosso esserti ancora d'aiuto?"

    textToSpeech = "La situazione aggiornata è:\n"

    textToSpeech += "{} {} rispetto a ieri;" \
        .format(today_vs_yesterday_positive,
                " caso positivo in più" if today_vs_yesterday_positive == 1 else "casi positivi in più" if today_vs_yesterday_positive > 0 else "casi positivi")

    textToSpeech += "\n{} {} rispetto a ieri;" \
        .format(today_vs_yesterday_dead,
                " decesso in più" if today_vs_yesterday_dead == 1 else "decessi in più" if today_vs_yesterday_dead > 0 else "decessi")

    textToSpeech += "\n{} {} rispetto a ieri." \
        .format(today_vs_yesterday_healed,
                "dimesso dall'ospedale e guarito in più" if today_vs_yesterday_healed == 1 else "dimessi dall'ospedale e guariti in più" if today_vs_yesterday_healed > 0 else "dimessi e guariti")

    textToSpeech += "\n\nPosso esserti ancora d'aiuto?"

    return textToSpeech, displayText


def __make__today_regional_stats_facebook_response__(data, date):  # TODO: implement method for facebook
    return "Facebook not implemented yet!"


def __make__today_national_stats_facebook_response__(data, date):  # TODO: implement method for facebook
    return "Facebook not implmented yet!"


def __make_today__provincial_stats_google_response__(data, date): # TODO: implement method for facebokk
    return "Facebook not implmented yet!"

def __trentinoFix__(df):
    """
    Region Trentino-Alto Adife is divide in to sub region P.A. Trentio e P.A. Bolzano
    :param region:
    _:param df
    :return:
    """
    df_bo = df[df[REGION_NAME] == PA_BOLZANO]
    df_tr = df[df[REGION_NAME] == PA_TRENTO]
    df_bo = df_bo.append(df_tr).sum()
    df_return = a = pd.DataFrame(df_bo.values.reshape(1, 19), columns=df_bo.index.values)
    return df_return


def createNewInfectsGraph():
    fig1 = go.Figure()

    url = "https://raw.githubusercontent.com/pcm-dpc/COVID-19/master/dati-andamento-nazionale/dpc-covid19-ita-andamento-nazionale.csv"
    df_today = pd.read_csv(url, error_bad_lines=False)

    fig1.add_trace(go.Scatter(x=df_today['data'], y=df_today['nuovi_positivi'],
                              mode='lines+markers', name="Andamento infezione", line=dict(color="#67c0be")))

    fig1.update_layout(title={"text": "Andamendo giornaliero dell'infezione"}, font=dict(color="#67c0be"),
                       xaxis_title="Giorni", yaxis_title="Nuovi positivi", plot_bgcolor='rgba(0,0,0,1)',
                       paper_bgcolor='rgba(0,0,0,1)')
    fig1.update_xaxes(gridcolor='rgba(0,0,0,1)')
    fig1.update_yaxes(gridcolor='rgba(0,0,0,1)')

    pio.write_image(fig1, './filename.svg', width=700, height=775)

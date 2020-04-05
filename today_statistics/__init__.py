import pandas as pd
from datetime import date, datetime, timedelta
from urllib.error import HTTPError

# constants to access csv data
DIMESSI = "dimessi_guariti"
NUOVI_POSITIVI = "variazione_totale_positivi"
DECEDUTI = "deceduti"
REGION_NAME = "denominazione_regione"
PROVINCE_NAME = "denominazione_provincia"

# fix trentino sub region
TRENTINO_ALTO_ADIGE = "Trenitino-Alto Adige"
PA_BOLZANO = "P.A. Bolzano"
PA_TRENTO = "P.A. Trento"

# const for index name
TODAY = "today"
YESTERDAY = "yesterday"


# TODO: create a method that retrive github document and remove duplicated code

def get_today_national_stats(params):
    """
    Retrive statistics about today and yesterday from Protezione Civile on github.
    Link: https://github.com/pcm-dpc/COVID-19
    :return: string for googleResponse textToSpeech and Facebook
    """
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

    return __make_today_national_stats_google_response__(df_toRecap), \
           __make__today_national_stats_facebook_response__(df_toRecap)


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
    return __make__today_regional_stats_google_response__(df_toRecap), \
           __make__today_regional_stats_facebook_response__(df_toRecap)


def get_today_province_stats(params):
    province = params.get("province")
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

    df_today = df_today[df_today[PROVINCE_NAME] == province]
    df_today.rename(index={df_today.index.values[0]: TODAY}, inplace=True)  # rename the index with today
    df_yesterday = pd.read_csv(url_yesterday, error_bad_lines=False)
    df_yesterday = df_yesterday[df_yesterday[PROVINCE_NAME] == province]
    df_yesterday.rename(index={df_yesterday.index.values[0]: YESTERDAY}, inplace=True)

    df_toRecap = df_today.append(df_yesterday)
    return __make__today_regional_stats_google_response__(df_toRecap), \
           __make__today_regional_stats_facebook_response__(df_toRecap)


def __make_today_national_stats_google_response__(data):
    today_vs_yesterday_positive = data[NUOVI_POSITIVI].loc[TODAY] - data[NUOVI_POSITIVI].loc[YESTERDAY]
    today_vs_yesterday_dead = data[DECEDUTI].loc[TODAY] - data[DECEDUTI].loc[YESTERDAY]
    today_vs_yesterday_healed = data[DIMESSI].loc[TODAY] - data[DIMESSI].loc[YESTERDAY]
    displayText = "Situazione aggiornata:\n"

    displayText += "🔴 {} nuovi casi positivi, {} {} rispetto a ieri;" \
        .format(data[NUOVI_POSITIVI].loc[TODAY], today_vs_yesterday_positive,
                " caso in più" if today_vs_yesterday_positive == 1 else "casi in più" if today_vs_yesterday_positive > 0 else "")

    displayText += "\n☠️ {} persone decedute, {} {} rispetto a ieri;" \
        .format(data[DECEDUTI].loc[TODAY], today_vs_yesterday_dead,
                " caso in più" if today_vs_yesterday_dead == 1 else "casi in più" if today_vs_yesterday_dead > 0 else "")

    displayText += "\n💚 {} dimessi dagli ospedali e guariti, {} {} rispetto a ieri." \
        .format(data[DIMESSI].loc[TODAY], today_vs_yesterday_healed,
                " caso in più" if today_vs_yesterday_healed == 1 else "casi in più" if today_vs_yesterday_healed > 0 else "")

    displayText += "\n Posso esserti ancora d'aiuto?"

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

    textToSpeech += "\n Posso esserti ancora d'aiuto?"

    return textToSpeech, displayText


def __make__today_regional_stats_google_response__(data):
    today_vs_yesterday_positive = data[NUOVI_POSITIVI].loc[TODAY] - data[NUOVI_POSITIVI].loc[YESTERDAY]
    today_vs_yesterday_dead = data[DECEDUTI].loc[TODAY] - data[DECEDUTI].loc[YESTERDAY]
    today_vs_yesterday_healed = data[DIMESSI].loc[TODAY] - data[DIMESSI].loc[YESTERDAY]
    # print(data)
    # data[REGION_NAME].loc[TODAY]
    displayText = "Situazione aggiornata:\n"

    displayText += "🔴 {} nuovi casi positivi, {} {} rispetto a ieri;" \
        .format(data[NUOVI_POSITIVI].loc[TODAY], today_vs_yesterday_positive,
                " caso in più" if today_vs_yesterday_positive == 1 else "casi in più" if today_vs_yesterday_positive > 0 else "")

    displayText += "\n☠️ {} persone decedute, {} {} rispetto a ieri;" \
        .format(data[DECEDUTI].loc[TODAY], today_vs_yesterday_dead,
                " caso in più" if today_vs_yesterday_dead == 1 else "casi in più" if today_vs_yesterday_dead > 0 else "")

    displayText += "\n💚 {} dimessi dagli ospedali e guariti, {} {} rispetto a ieri." \
        .format(data[DIMESSI].loc[TODAY], today_vs_yesterday_healed,
                " caso in più" if today_vs_yesterday_healed == 1 else "casi in più" if today_vs_yesterday_healed > 0 else "")

    displayText += "\n Posso esserti ancora d'aiuto?"

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

    textToSpeech += "\n Posso esserti ancora d'aiuto?"

    return textToSpeech, displayText


def __make__today_regional_stats_facebook_response__(data):  # TODO: implement method for facebook
    return "Facebook not implemented yet!"


def __make__today_national_stats_facebook_response__(data):  # TODO: implement method for facebook
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
    df_return = a = pd.DataFrame(df_bo.values.reshape(1, 19), columns = df_bo.index.values)
    return df_return


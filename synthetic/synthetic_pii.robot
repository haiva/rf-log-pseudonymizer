*** Settings ***
Documentation       Synteettinen testisarja, joka sijoittaa known_pii.py:n arvot kaikkialle,
...                 minne henkilötiedot oikeissa tuloksissa päätyvät. Testi "Tarkistus
...                 Epäonnistuu" epäonnistuu tarkoituksella.
Variables           known_pii.py
Metadata            Ympäristö    palvelin ${IP2}, ylläpito ${EMAIL2}


*** Test Cases ***
Kirjautuminen Ja Istunto
    [Documentation]    Kirjautumispyyntö käsiteltiin palvelimella ${IP}.
    [Tags]    asiakas-${USER_UUID}
    Log    GET https://api.example.com/v1/users?token=${SESSION_TOKEN}&uid=${USER_UUID}
    Log    Authorization: Bearer ${JWT}
    Log    Cookie: sessionid=${SESSION_TOKEN}; lang=fi
    Log    Epäonnistunut kirjautuminen käyttäjältä ${EMAIL2} osoitteesta ${IP2}    WARN
    # Argumentit tallentuvat output.xml:ään kirjoitetussa muodossa, joten tässä literaalit
    # (samat arvot kuin known_pii.py:n EMAIL ja HETU_2000).
    Hae Asiakas    matti.meikalainen@example.com    010105A967X
    Kirjaudu käyttäjänä tiina.testaaja@example.org

Avaimet Ja Salaisuudet
    Log    GET https://api.example.com/v1/data?api_key=${API_KEY}
    Log    X-API-Key: ${PROVIDER_KEY}
    Log    Authorization: Basic ${BASIC_AUTH}
    Log    Vastaus: {"client_secret": "${CLIENT_SECRET}", "refresh_token": "${REFRESH_TOKEN}"}
    Log    Yhdistetään tietokantaan: user=testaaja password=${PASSWORD}

Henkilötiedot Muuttujissa
    ${hetu}=    Set Variable    ${HETU_1900}
    VAR    ${puhelin}    ${PHONE}
    Log    Asiakas ${hetu}, puhelin ${puhelin}, sähköposti ${EMAIL}
    # Pitkän viestin RF pakkaa log.html:ssä (zlib + base64), jolloin arvot eivät näy selväkielisinä.
    ${tayte}=    Evaluate    ' '.join(['vastausrivi'] * 60)
    Log    Vastausrunko: email=${EMAIL2} ip=${IP} hetu=${HETU_2000} ${tayte}

Upotettu Kuva
    Log    Kuvakaappaus käyttäjän ${EMAIL} näkymästä: ${IMAGE_HTML}    html=True

Tarkistus Epäonnistuu
    Should Be Equal    ${EMAIL}    ${EMAIL2}


*** Keywords ***
Hae Asiakas
    [Arguments]    ${sahkoposti}    ${hetu}
    Log    Haetaan asiakas ${sahkoposti} (${hetu})

Kirjaudu käyttäjänä ${kayttaja}
    Log    Kirjaudutaan: ${kayttaja}

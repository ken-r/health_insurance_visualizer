from shiny import App, reactive, render, ui
import pandas as pd

# Mapping the codes from the dataset to their actual names.
# I only found a pdf file with this information, so I manually created this dictionary.
# Source: https://www.bag.admin.ch/dam/de/sd-web/tGi8dHtom8eb/Zugelassene%20Krankenversicherer_1.10.2025.pdf
# TODO: There is actually an xlsx file with this information: https://www.bag.admin.ch/dam/de/sd-web/Gjlbd6ULgWmm/Zugelassene%20Krankenversicherer_1.10.2025.xlsx
BAG_VERSICHERER = {
    1560: "Agrisano",
    1507: "AMB Assurances SA",
    32:   "Aquilana",
    1542: "Assura-Basis SA",
    312:  "Atupri Gesundheitsversicherung AG",
    343:  "Avenir Krankenversicherung AG",
    1322: "Birchmeier",
    290:  "CONCORDIA",
    8:    "CSS",
    881:  "EGK",
    134:  "Einsiedler Krankenkasse",
    1386: "GALENOS AG",
    780:  "Glarner",
    1562: "Helsana",
    829:  "KLuG",
    376:  "KPT",
    820:  "Lumneziana",
    360:  "Luzerner Hinterland",
    1479: "Mutuel Assurance Maladie SA",
    455:  "ÖKK",
    1535: "Philos",
    1401: "rhenusana",
    1568: "sana24",
    901: "sanavals",
    1509: "Sanitas",
    923: "SLKK",
    941: "sodalis",
    246: "Steffisburg",
    194: "Sumiswalder",
    1384: "SWICA",
    1113: "Vallée d’Entremont",
    1555: "Visana",
    1040: "Visperterminen",
    966: "vita surselva",
    1570: "Vivacare",
    509: "Vivao Sympany",
    1318: "Wädenswil",
}

MAX_AMOUNT_AFTER_FRANCHISE = 700
DECIMAL_AFTER_FRANCHISE = 0.10 # We need to pay 10% of costs after franchise

CHILD_LVL_TO_AMOUNT = {"FRAST1": 0, "FRAST2": 100, "FRAST3": 200, "FRAST4": 300, "FRAST5": 400, "FRAST6": 500, "FRAST7": 600}
ADULT_LVL_TO_AMOUNT = {"FRAST1": 300, "FRAST2": 500, "FRAST3": 1000, "FRAST4": 1500, "FRAST5": 2000, "FRAST6": 2500}

# Load data once when app starts (outside server function)
try:
    premiums_df = pd.read_csv("https://opendata.bagnet.ch/?r=/download&path=L1ByYWVtaWVuL1Byw6RtaWVuX0NILmNzdg%3D%3D")
    premiums_df['Versicherung'] = premiums_df['Versicherer'].map(BAG_VERSICHERER)


    premium_regions_df = pd.read_excel("https://www.priminfo.admin.ch/downloads/praemienregionen.xlsx", sheet_name='A_COM', skiprows=4,engine="openpyxl")

    # The original excel file has column names on two lines: First Line = German name, Second Line = French translation
    premium_regions_df.columns = [col.splitlines()[0] for col in premium_regions_df.columns]
    print("Loaded data successfully.")

except Exception as e:
    print(f"Error loading data: {e}")

# Calculate count of each PLZ and append as a new column
premium_regions_df['plz_count'] = premium_regions_df.groupby('PLZ')['PLZ'].transform('count')


app_ui = ui.page_fluid(
        ui.input_numeric("birth_year", "Birth Year", value=1990, min=1910, max=2024),
        ui.output_ui("municipality_select"),
        ui.output_ui("franchise_select"),
        ui.input_radio_buttons(
            "accident_insurance",
            "Do you need to include accident insurance?",
            choices={"MIT-UNF": "Yes", "OHN-UNF": "No"},
            selected="MIT-UNF"  # or "UNF-NEIN" / "UNF-JA" as default
        ),
        ui.input_action_button("calculate_offers", "Calculate"),
    ui.card(
        ui.card_header("Insurance Cost Comparison"),
        ui.output_data_frame("insurance_table")
    ),
)

def server(input, output, session):
    
    @reactive.calc
    def is_child():
        return input.birth_year() >= 2008

    @reactive.calc
    def age_category():
        if is_child():
            return 'AKL-KIN'
        elif input.birth_year() >= 2001:
            return 'AKL-JUG'
        else:
            return 'AKL-ERW'
        
    @reactive.calc
    def franch_lvl_to_franch_amount():
        return CHILD_LVL_TO_AMOUNT[input.franchise_select()] if is_child() else ADULT_LVL_TO_AMOUNT[input.franchise_select()]
        
    
    @render.ui
    def municipality_select():
        return ui.input_selectize(
            "location",
            "Enter Postal Code or Municipality:",
            choices={"": ""} | {f"{row['Kanton']}|{row['Region']}|{row['PLZ']}|{row['Ort']}|{row['Gemeinde']}": f"{row['PLZ']} {row['Ort']}" + (f" (Gemeinde {row['Gemeinde']})" if row['plz_count'] > 1 else "")
                for _, row in premium_regions_df.iterrows()
            }, 
            # By default, we want the selection to be empty. But the empty option
            # should not be shown in the dropdown list.
            options={"allowEmptyOption": True, "showEmptyOptionInDropdown": False},
            selected=""
        )
    
    @render.ui
    def franchise_select():
        if is_child():
            # Children franchise options
            franchise_options = {
                "FRAST1": "CHF 0",
                "FRAST2": "CHF 100", 
                "FRAST3": "CHF 200",
                "FRAST4": "CHF 300",
                "FRAST5": "CHF 400",
                "FRAST6": "CHF 500",
                "FRAST7": "CHF 600"
            }
        else:
            franchise_options = {
                "FRAST1": "CHF 300",
                "FRAST2": "CHF 500", 
                "FRAST3": "CHF 1000",
                "FRAST4": "CHF 1500",
                "FRAST5": "CHF 2000",
                "FRAST6": "CHF 2500"
            }
        
        return ui.input_select(
            "franchise",
            "Franchise",
            choices=franchise_options,
            selected="FRAST1"
        )
    

    # Reactive expression triggered only when button is clicked
    @reactive.event(input.calculate_offers)
    def calculate_data():
        df = pd.DataFrame()
        canton, region, *_, = input.location().split('|')

        df = premiums_df[(premiums_df['Kanton'] == canton) & 
                           (premiums_df['Region'] == f"PR-REG CH{region}") & 
                           (premiums_df['Altersklasse'] == age_category()) &
                           (premiums_df['Franchisestufe'] == input.franchise()) &
                           (premiums_df['Unfalleinschluss'] == input.accident_insurance())][['Versicherung', 'Tarif', 'Prämie']]

        return df


    @render.data_frame
    def insurance_table():
        return calculate_data()
    

app = App(app_ui, server)

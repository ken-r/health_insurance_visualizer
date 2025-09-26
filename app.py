from shiny import App, reactive, render, ui
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# Mapping the codes from the dataset to their actual names.
# I only found a pdf file with this information, so I manually created this dictionary.
# Source: https://www.bag.admin.ch/dam/de/sd-web/tGi8dHtom8eb/Zugelassene%20Krankenversicherer_1.10.2025.pdf
# TODO: There is actually an xlsx file with this information: https://www.bag.admin.ch/dam/de/sd-web/Gjlbd6ULgWmm/Zugelassene%20Krankenversicherer_1.10.2025.xlsx
BAG_VERSICHERER = {
    1560: "Agrisano",
    1507: "AMB Assurances SA",
    32:   "Aquilana",
    1542: "Assura",
    312:  "Atupri",
    343:  "Avenir",
    1322: "Birchmeier",
    290:  "CONCORDIA",
    8:    "CSS",
    881:  "EGK",
    134:  "Einsiedler",
    1386: "GALENOS AG",
    780:  "Glarner",
    1562: "Helsana",
    829:  "KLuG",
    376:  "KPT",
    820:  "Lumneziana",
    360:  "KKLH",
    1479: "Mutuel",
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

municipality_choices = {'': ''} | {f"{row['Kanton']}|{row['Region']}|{row['PLZ']}|{row['Ort']}|{row['Gemeinde']}": f"{row['PLZ']} {row['Ort']}" + (f" (Gemeinde {row['Gemeinde']})" if row['plz_count'] > 1 else "")
                for _, row in premium_regions_df.iterrows()}

app_ui = ui.page_fixed( 
        ui.panel_title("Swiss Health Insurance Premium Visualizer"),
        ui.output_ui("dynamic_page"),
        )
        
def server(input, output, session):
    page_state = reactive.Value('landing')
    personal_details = reactive.Value({})

    @render.ui
    def dynamic_page():
        if page_state() == 'landing':
            return ui.card(
                ui.input_numeric("birth_year", "Year of birth", value=2000, min=1910, max=2024),
                ui.output_ui("municipality_select"),
                ui.output_ui("franchise_select"),
                ui.input_radio_buttons(
                    "accident_insurance",
                    "Include accident insurance?",
                    choices={"MIT-UNF": "Yes", "OHN-UNF": "No"},
                    selected="MIT-UNF"
                ),
                ui.input_action_button("calculate_offers", "Calculate Insurance Offers")
            )
        elif page_state() == 'results':
            personal_details_locked = personal_details.get()
            return ui.card(
                ui.h4("Entered Personal Details"),
                ui.p(f"Year of birth: {personal_details_locked['birth_year']}"),
                ui.p(f"Municipality: {location_display()}"),
                ui.p(f"Franchise: {franchise_display()}"),
                ui.p(f"Accident insurance: {accident_display()}"),
                ui.input_action_button("modify_details", "Modify"),
                ui.card_header("Insurance Cost Comparison"),
                ui.output_data_frame("insurance_table"),
                ui.output_plot("franchises_comparison_plot")
            )


    @reactive.effect
    @reactive.event(input.calculate_offers)
    def store_details():
        # TODO: Add input checks
        personal_details.set({
            "birth_year": input.birth_year(),
            "location": input.location(),
            "franchise": input.franchise(),
            "accident_insurance": input.accident_insurance()
        })
        page_state.set('results')
    
    @reactive.effect
    @reactive.event(input.modify_details)
    def back_to_landing():
        page_state.set('landing')

    @reactive.calc
    def is_child():
        return personal_details.get()['birth_year'] >= 2008

    @reactive.calc
    def age_category():
        if is_child():
            return 'AKL-KIN'
        elif input.birth_year() >= 2001:
            return 'AKL-JUG'
        else:
            return 'AKL-ERW'
        
    @reactive.calc
    def franchise_display():
        return f"{franchise_amount()} CHF"
    
    @reactive.calc
    def franchise_amount():
        franchise_lvl = personal_details.get()['franchise']
        return CHILD_LVL_TO_AMOUNT[franchise_lvl] if is_child() else ADULT_LVL_TO_AMOUNT[franchise_lvl]
    
    def franchise_amount_for_person(franchise_level, age_class):
        return CHILD_LVL_TO_AMOUNT[franchise_level] if age_class == 'AKL-KIN' else ADULT_LVL_TO_AMOUNT[franchise_level]

    @reactive.calc
    def location_display():
        loc_code = personal_details.get()['location']
        return municipality_choices[loc_code]
    
    @reactive.calc
    def accident_display():
        return "Yes" if personal_details.get()['accident_insurance'] == "MIT-UNF" else "No"

    @render.ui
    def municipality_select():
        return ui.input_selectize(
            "location",
            "Enter Postal Code or Municipality:",
            choices=municipality_choices, 
            # By default, we want the selection to be empty. But the empty option
            # should not be shown in the dropdown list.
            options={"allowEmptyOption": True, "showEmptyOptionInDropdown": False},
            selected=""
        )
    
    @reactive.calc
    def age_validation():   
        birth_year = input.birth_year()
        return birth_year is not None and isinstance(birth_year, int) and 1900 <= birth_year <= 2025

    @render.ui
    def franchise_select():
        birth_year = input.birth_year()
        if not age_validation():
            return ui.div(
                ui.tags.label("Franchise", class_="form-label"),
                ui.tags.select(
                    disabled=True,
                    title="Please enter your birth year.",
                    class_="form-select",
                    style="opacity: 0.6;"
                ),
                class_="form-group shiny-input-container"
                ) 
        franchise_options = ADULT_LVL_TO_AMOUNT if birth_year < 2008 else CHILD_LVL_TO_AMOUNT

        return ui.input_select(
            "franchise",
            "Franchise",
            choices=franchise_options,
            selected=None
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
                           (premiums_df['Unfalleinschluss'] == input.accident_insurance())].sort_values(by='Prämie')

        return df


    @render.data_frame
    def insurance_table():
        return render.DataGrid(
            calculate_data()[['Versicherung', 'Tarifbezeichnung', 'Prämie']], 
            selection_mode="row"
        )

    @render.plot
    def franchises_comparison_plot():
        selected = input.insurance_table_selected_rows()

        # # Debug information
        # print(f"Selected rows: {selected}")
        # print(f"Type: {type(selected)}")
        # print(f"Length: {len(selected) if selected else 'None/Empty'}")

        if not selected:
            return None
        
        df = calculate_data()
        row = df.iloc[selected[0]]
        insurance_provider, insurance_plan = row['Versicherung'], row['Tarifbezeichnung']
        
        franchise_levels_to_compare = premiums_df[
            (premiums_df['Versicherung'] == insurance_provider) &
            (premiums_df['Tarifbezeichnung'] == insurance_plan) &
            (premiums_df['Unfalleinschluss'] == row['Unfalleinschluss']) &
            (premiums_df['Kanton'] == row['Kanton']) &
            (premiums_df['Region'] == row['Region']) &
            (premiums_df['Altersklasse'] == row['Altersklasse'])
        ]

        # Create treatment costs range (0 to 10,000 CHF)
        treatment_costs = np.linspace(0, 10000, 1000)

        fig, ax = plt.subplots(figsize=(8, 5))


        for _, franchise_row in franchise_levels_to_compare.iterrows():    
            premium_amount = franchise_row['Prämie']
            franchise_amount = franchise_amount_for_person(franchise_row['Franchisestufe'], row['Altersklasse'])
            annual_costs = np.array([
                calculate_annual_cost(x, franchise_amount, premium_amount)
                for x in treatment_costs
            ])

            ax.plot(treatment_costs, annual_costs, label=f'Franchise {franchise_amount} CHF')

        ax.set_xlabel('Treatment Costs (CHF)')
        ax.set_ylabel('Total Costs for You (CHF)')
        ax.set_title(f'Annual Total Costs for You: {insurance_provider} - {insurance_plan}')
        ax.legend()
        ax.grid(True)

        return fig
      
    
    def calculate_annual_cost(treatment_costs, franchise_level, premium):
        amount_after_franchise = max(0, treatment_costs - franchise_level)
        costs_to_cover_after_franchise = min(amount_after_franchise * DECIMAL_AFTER_FRANCHISE, MAX_AMOUNT_AFTER_FRANCHISE)
        total_treatment_costs_to_cover = min(treatment_costs, franchise_level) + costs_to_cover_after_franchise
        total_cost = total_treatment_costs_to_cover + 12 * premium
        return total_cost

app = App(app_ui, server)

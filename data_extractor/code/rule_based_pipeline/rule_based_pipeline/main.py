# ============================================================================================================================
# PDF_Analyzer
# File   : main.py
# Author : Ismail Demir (G124272)
# Date   : 12.06.2020
# ============================================================================================================================


from AnalyzerDirectory import *
from KPIResultSet import *
from TestData import *
from DataImportExport import *
import config
from data_extractor.code.rule_based_pipeline.rule_based_pipeline.test import test_prepare_kpispecs

# Constants Variables
DEFAULT_YEAR = 2022


def parse_arguments():
    """
    Parse command-line arguments and set global configuration variables.

    Returns:
        None
    """
    parser = argparse.ArgumentParser(description='Rule-based KPI extraction')
    parser.add_argument('--input_folder', type=str, default=config.global_input_folder,
                        help='Folder where PDFs are stored')
    parser.add_argument('--working_folder', type=str, default=config.global_working_folder,
                        help='Folder where working files are stored')
    parser.add_argument('--output_folder', type=str, default=config.global_output_folder,
                        help='Folder where output is stored')
    parser.add_argument('--verbosity', type=int, default=config.global_verbosity,
                        help='Verbosity level (0=shut up)')
    # new optional arguments (for Debugging mode):
    parser.add_argument('--name_of_pdf', type=str, default=config.global_name_of_pdf,
                        help='Filter Specific PDF')
    parser.add_argument('--page_of_pdf', type=str, default=config.global_page_of_pdf,
                        help='Specific page of the PDF')


def fix_config_paths():
    """
    Fix global paths in the configuration.
    This function sets the global paths based on the current directory.

    Returns:
        None
    """
    try:
        path = globals()['_dh'][0]
    except KeyError:
        path = os.path.dirname(os.path.realpath(__file__))
    path = remove_trailing_slash(path).replace('\\', '/')
    config.global_exec_folder = path + r'/'
    config.global_rendering_font_override = path + r'/' + config.global_rendering_font_override


def print_configuration():
    """
    Print configuration information.

    Returns:
        None
    """
    print_verbose(1, "Using config.global_exec_folder=" + config.global_exec_folder)
    print_verbose(1, "Using config.global_input_folder=" + config.global_input_folder)
    print_verbose(1, "Using config.global_working_folder=" + config.global_working_folder)
    print_verbose(1, "Using config.global_output_folder=" + config.global_output_folder)
    print_verbose(1, "Using config.global_verbosity=" + str(config.global_verbosity))
    print_verbose(1, "Using config.global_rendering_font_override=" + config.global_rendering_font_override)
    # new optional arguments (for Debugging mode):
    print_verbose(1, "Using config.global_name_of_pdf=" + config.global_name_of_pdf)
    print_verbose(1, "Using config.global_page_of_pdf=" + config.global_page_of_pdf)


def analyze_and_save_results(pdf_name, kpis, info_file_contents):
    """
    Analyze the specified PDF, save the results, and print verbose information.

    Args:
        pdf_name (str): The name of the PDF file.
        kpis (list): List of KPI specifications.
        info_file_contents (dict): Information loaded from an info file.

    Returns:
        KPIResultSet: Results of the analysis.
    """
    kpi_results = KPIResultSet(kpimeasures=[])
    # Modify * in wildcard_restrict_page in order to analyze specific page, e.g.:  *00042
    cur_kpi_results = analyze_pdf(config.global_input_folder + pdf_name, kpis, DEFAULT_YEAR, info_file_contents, wildcard_restrict_page='*')
    kpi_results.extend(cur_kpi_results)
    kpi_results.save_to_csv_file(config.global_output_folder + pdf_name + r'.csv')
    print_verbose(1, "RESULT FOR " + pdf_name)
    print_verbose(1, kpi_results)
    return kpi_results


def generate_dummy_test_data():
    test_data = TestData()
    test_data.generate_dummy_test_data(config.global_input_folder)
    return test_data


def analyze_pdf(pdf_file, kpis, default_year, info_file_contents, wildcard_restrict_page='*', force_pdf_convert=False,
                force_parse_pdf=False, assume_conversion_done=False, do_wait=False):
    print_verbose(1, "Analyzing PDF: " + str(pdf_file))

    guess_year = Format_Analyzer.extract_year_from_text(pdf_file)
    if guess_year is None:
        guess_year = default_year

    html_dir_path = get_html_out_dir(pdf_file)
    os.makedirs(html_dir_path, exist_ok=True)

    reload_necessary = True

    if not assume_conversion_done:
        # convert pdf to html
        print_big("Convert PDF to HTML", do_wait)
        if force_pdf_convert or not file_exists(html_dir_path + '/index.html'):
            HTMLDirectory.convert_pdf_to_html(pdf_file, info_file_contents)

        # return KPIResultSet() # STOP after converting PDF files (don't continue with analysis)

        # parse and create json and png
        print_big("Convert HTML to JSON and PNG", do_wait)
        # print(html_dir_path)
        dir = HTMLDirectory()
        if (force_parse_pdf or get_num_of_files(html_dir_path + '/jpage*.json') != get_num_of_files(
                html_dir_path + '/page*.html')):
            dir.parse_html_directory(get_html_out_dir(pdf_file), 'page*.html')  # ! page*
            dir.render_to_png(html_dir_path, html_dir_path)
            dir.save_to_dir(html_dir_path)
            if wildcard_restrict_page == '*':
                reload_necessary = False

    # return KPIResultSet()# STOP after parsing HTML files (don't continue with analysis)

    # load json files
    print_big("Load from JSON", do_wait)
    if reload_necessary:
        dir = HTMLDirectory()
        dir.load_from_dir(html_dir_path, 'jpage' + str(wildcard_restrict_page) + '.json')

    # analyze
    print_big("Analyze Pages", do_wait)
    ana = AnalyzerDirectory(dir, guess_year)
    # kpis = test_prepare_kpispecs()
    # print(kpis)

    kpi_results = KPIResultSet(ana.find_multiple_kpis(kpis))

    print_big("FINAL RESULT FOR: " + str(pdf_file.upper()), do_wait=False)
    print_verbose(1, kpi_results)

    return kpi_results


def get_input_variable(val, desc):
    if val is None:
        val = input(desc)

    if val is None or val == "":
        print("This must not be empty")
        sys.exit(0)

    return val


def main():
    # Parse command-line arguments
    parse_arguments()

    # Fix global paths
    fix_config_paths()

    # Print configuration information
    print_configuration()

    # Generate dummy test data
    test_data = generate_dummy_test_data()

    # Filter PDF
    test_data.filter_kpis(by_source_file=['T_Rowe_Price_2021_EN.pdf'])

    # Print information about the test data
    print_big("Data-set", False)
    print_verbose(1, test_data)

    # Get a list of PDFs from the test data
    pdfs = test_data.get_fixed_pdf_list()
    print_verbose(1, 'Related (fixed) PDFs: ' + str(pdfs) + ', in total : ' + str(len(pdfs)))
    # return # (only for Debugging purpose) I will delete it

    # Prepare KPI specifications
    kpis = test_prepare_kpispecs()

    # Initialize overall KPI results
    overall_kpi_results = KPIResultSet()

    # Load information from the file info.json
    info_file_contents = DataImportExport.load_info_file_contents(remove_trailing_slash(config.global_working_folder)
                                                                  + '/info.json')

    # Record the start time for performance measurement
    time_start = time.time()

    # Iterate over each PDF in the list
    for pdf in pdfs:
        # Analyze the current PDF
        kpi_results = analyze_and_save_results(pdf, kpis, info_file_contents)
        overall_kpi_results.extend(kpi_results)

    # Record the finish time for performance measurement
    time_finish = time.time()

    # Print the final overall result
    print_big("FINAL OVERALL-RESULT", do_wait=False)
    print_verbose(1, overall_kpi_results)

    # Save overall KPI results to a CSV file
    overall_kpi_results.save_to_csv_file(config.global_output_folder + r'kpiresults_tmp.csv')

    # Calculate and print the total run-time
    total_time = time_finish - time_start
    print_verbose(1, "Total run-time: " + str(total_time) + " sec ( " + str(total_time / max(len(pdfs), 1)) + " sec per PDF)")


# Entry point of the program
if __name__ == "__main__":
    main()

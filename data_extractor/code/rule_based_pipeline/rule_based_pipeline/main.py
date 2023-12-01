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
from data_extractor.code.rule_based_pipeline.rule_based_pipeline.test import test_prepare_kpispecs, load_test_data


def generate_dummy_test_data():
    test_data = TestData()
    test_data.generate_dummy_test_data(config.global_raw_pdf_folder, '*')
    # print("DATA-SET:")
    # print(test_data)
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

    # return KPIResultSet()# STOP after parsing HTML files (dont continue with analysis)

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
    DEFAULT_YEAR = 2024

    parser = argparse.ArgumentParser(description='Rule-based KPI extraction')
    # Add the arguments
    parser.add_argument('--raw_pdf_folder',
                        type=str,
                        default=None,
                        help='Folder where PDFs are stored')
    parser.add_argument('--working_folder',
                        type=str,
                        default=None,
                        help='Folder where working files are stored')
    parser.add_argument('--output_folder',
                        type=str,
                        default=None,
                        help='Folder where output is stored')
    parser.add_argument('--verbosity',
                        type=int,
                        default=1,
                        help='Verbosity level (0=shut up)')
    args = parser.parse_args()
    config.global_raw_pdf_folder = remove_trailing_slash(
        get_input_variable(args.raw_pdf_folder, "What is the raw pdf folder?")).replace('\\', '/') + r'/'
    config.global_working_folder = remove_trailing_slash(
        get_input_variable(args.working_folder, "What is the working folder?")).replace('\\', '/') + r'/'
    config.global_output_folder = remove_trailing_slash(
        get_input_variable(args.output_folder, "What is the output folder?")).replace('\\', '/') + r'/'
    config.global_verbosity = args.verbosity

    os.makedirs(config.global_working_folder, exist_ok=True)
    os.makedirs(config.global_output_folder, exist_ok=True)

    # fix config.global_exec_folder and config.global_rendering_font_override
    path = ''
    try:
        path = globals()['_dh'][0]
    except KeyError:
        path = os.path.dirname(os.path.realpath(__file__))
    path = remove_trailing_slash(path).replace('\\', '/')

    config.global_exec_folder = path + r'/'
    config.global_rendering_font_override = path + r'/' + config.global_rendering_font_override

    print_verbose(1, "Using config.global_exec_folder=" + config.global_exec_folder)
    print_verbose(1, "Using config.global_raw_pdf_folder=" + config.global_raw_pdf_folder)
    print_verbose(1, "Using config.global_working_folder=" + config.global_working_folder)
    print_verbose(1, "Using config.global_output_folder=" + config.global_output_folder)
    print_verbose(1, "Using config.global_verbosity=" + str(config.global_verbosity))
    print_verbose(5, "Using config.global_rendering_font_override=" + config.global_rendering_font_override)

    # test_data = load_test_data(r'test_data/aggregated_complete_samples_new.csv')
    test_data = generate_dummy_test_data()

    # For debugging, save csv:
    # test_data.save_to_csv(r'test_data/test_output_new.csv')
    # return

    # Filter PDF
    # test_data.filter_kpis(by_source_file = ['PGE_Corporation_CDP_Climate_Change_Questionnaire_2021.pdf'])

    print_big("Data-set", False)
    print_verbose(1, test_data)

    pdfs = test_data.get_fixed_pdf_list()

    print_verbose(1, 'Related (fixed) PDFs: ' + str(pdfs) + ', in total : ' + str(len(pdfs)))
    # return # TODO: Uncomment this line, to return immediately, after PDF list has been shown. ###

    kpis = test_prepare_kpispecs()  # TODO: In the future, KPI specs should be loaded from "nicer" implemented source, e.g., JSON file definition

    overall_kpi_results = KPIResultSet()

    info_file_contents = DataImportExport.load_info_file_contents(
        remove_trailing_slash(config.global_working_folder) + '/info.json')

    time_start = time.time()

    for pdf in pdfs:
        kpi_results = KPIResultSet(kpimeasures=[])
        cur_kpi_results = analyze_pdf(config.global_raw_pdf_folder + pdf, kpis, DEFAULT_YEAR, info_file_contents,
                                      wildcard_restrict_page='*', assume_conversion_done=False,
                                      force_parse_pdf=False)  # TODO:  Modify * in order to analyze specific page, e.g.:  *00042 ###
        kpi_results.extend(cur_kpi_results)
        overall_kpi_results.extend(cur_kpi_results)
        kpi_results.save_to_csv_file(config.global_output_folder + pdf + r'.csv')
        print_verbose(1, "RESULT FOR " + pdf)
        print_verbose(1, kpi_results)

    time_finish = time.time()

    print_big("FINAL OVERALL-RESULT", do_wait=False)
    print_verbose(1, overall_kpi_results)

    overall_kpi_results.save_to_csv_file(config.global_output_folder + r'kpiresults_tmp.csv')

    total_time = time_finish - time_start
    print_verbose(1, "Total run-time: " + str(total_time) + " sec ( " + str(
        total_time / max(len(pdfs), 1)) + " sec per PDF)")


main()

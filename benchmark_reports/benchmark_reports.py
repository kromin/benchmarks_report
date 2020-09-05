import argparse
import json
import os
import time
from stat import *
from numpy import sum


class Model:
    """
    Model for MVP
    input: 'path', '.extension'

    Find files in specified path, collects data and amount
    """
    def __init__(self, path, extension='.json'):
        """Constructor creates variables 'names' and 'extension'"""
        self.__filenames = []
        for file in os.listdir(path):
            if file.endswith(extension):
                self.__filenames.append(file)
        self.path = path
        self.file_data = {}  # все данные со всех файлов в dict
        self.file_dates = []  # дата/время создания файлов

    def get_amount(self):
        """Get quantity of json files"""
        return len(self.__filenames)

    def get_data(self):
        """
        Get data from json files as dict where
        key=date, value=dict(benchmark_name: [real_time, cpu_time, time_unit])

        ex:
        self.file_data['02/28/20 01:41:45'].get('PortfolioFixture/ChangeOrderFutures/100/0/3')[0] = 8092.7246
        [0] = real_time, [1] = cpu_time, [2] = time_unit
        """
        for file in self.__filenames:
            with open(self.path + file, "r") as read_file:
                data = json.load(read_file)
            date = data.get("context").get("date")  # Получили дату создания json файла
            self.file_dates += [date]
            self.file_data[date] = {}
            b_data = dict()
            for benchmark in data["benchmarks"]:
                b_name = benchmark.get("name")
                real_time = benchmark.get("real_time")
                cpu_time = benchmark.get("cpu_time")
                time_unit = benchmark.get("time_unit")
                b_data[b_name] = [real_time, cpu_time, time_unit]
            self.file_data[date] = b_data


def calculate_change(old_val, new_val):
    """
    Return a float representing the decimal change between old_val and new_val.
    """
    if old_val == 0 and new_val == 0:
        return 0.0
    if old_val == 0:
        return float(new_val - old_val) / (float(old_val + new_val) / 2)
    return float(new_val - old_val) / abs(old_val)


def get_deltas(data_old, data_new):
    """
    Return a list of decimal changes between data_old and data_new
    get_deltas() = [delta_real_time, delta_cpu_time, time_unit]
    """
    units = {
        's': 1,
        'sec': 1,
        'ms': 10 ** -3,
        'us': 10 ** -6,
        'mcs': 10 ** -6,
        'ns': 10 ** -9,
        'ps': 10 ** -12
    }
    if data_new[2] == data_old[2]:
        return [calculate_change(data_old[0], data_new[0]), calculate_change(data_old[1], data_new[1]), data_old[2]]
    else:
        if data_new[2] in units and data_old[2] in units:
            data_old[0] = data_old[0] / units.get(data_old[2]) * 10 ** -9
            data_old[1] = data_old[1] / units.get(data_old[2]) * 10 ** -9
            data_new[0] = data_new[0] / units.get(data_new[2]) * 10 ** -9
            data_new[1] = data_new[1] / units.get(data_new[2]) * 10 ** -9
            data_new[2] = 'ns'
            data_old[2] = 'ns'
            return [calculate_change(data_old[0], data_new[0]), calculate_change(data_old[1], data_new[1]), data_old[2]]
        else:
            print('This time unit is not supported')
            exit(404)


class Presenter:
    """
    Presenter for MVP
    input: 'data' - from Model

    Compares and analyses benchmark data inside
    """
    def __init__(self, model):
        """Constructor"""
        self.model = model  # экземпляр класса Модель
        self.benchmark_names = self.get_benchmark_names()  # список названий бенчмарков
        self.deltas = []  # результаты попарного сравнения бенчмарков

        # суммы real и cpu времени для каждой версии между собой
        # для получения итогового отклонения относительно начальных данных
        self.sums = []

    def get_benchmark_names(self):
        """
        Return list of benchmark names
        """
        return list(self.model.file_data[self.model.file_dates[0]].keys())

    def compare(self):
        """
        Compare all files by pairs and prep values for View + calculate_sum()
        """
        for i in range(self.model.get_amount() - 1):
            data_old = []
            data_new = []
            data = []
            for name in self.benchmark_names:
                data_old += [self.model.file_data[self.model.file_dates[i]].get(name)]
                data_new += [self.model.file_data[self.model.file_dates[i + 1]].get(name)]
            for line in range(len(self.benchmark_names)):
                data += [get_deltas(data_old[line], data_new[line])]
            self.deltas += [data]
        self.sums = self.calculate_sum()

    def calculate_sum(self):
        """
        Calculate sums of all real_time and cpu_time by benchmark_names
        """
        sum_real_time = 0
        sum_cpu_time = 0
        sums = []
        # сумма всех бенчмарков по отдельности
        for data in range(len(self.benchmark_names)):
            for i in range(self.model.get_amount() - 1):
                sum_real_time += self.deltas[i][data][0]
                sum_cpu_time += self.deltas[i][data][1]
            sums += [[sum_real_time, sum_cpu_time]]
        return sums


class BenchmarkColor(object):
    def __init__(self, name, code):
        self.name = name
        self.code = code

    def __repr__(self):
        return '%s%r' % (self.__class__.__name__,
                         (self.name, self.code))

    def __format__(self, format):
        return self.code


BC_NONE = BenchmarkColor('NONE', '')
BC_MAGENTA = BenchmarkColor('MAGENTA', '\033[95m')
BC_CYAN = BenchmarkColor('CYAN', '\033[96m')
BC_OKBLUE = BenchmarkColor('OKBLUE', '\033[94m')
BC_OKGREEN = BenchmarkColor('OKGREEN', '\033[32m')
BC_HEADER = BenchmarkColor('HEADER', '\033[92m')
BC_WARNING = BenchmarkColor('WARNING', '\033[93m')
BC_WHITE = BenchmarkColor('WHITE', '\033[97m')
BC_FAIL = BenchmarkColor('FAIL', '\033[91m')
BC_ENDC = BenchmarkColor('ENDC', '\033[0m')
BC_BOLD = BenchmarkColor('BOLD', '\033[1m')
BC_UNDERLINE = BenchmarkColor('UNDERLINE', '\033[4m')


def choose_color(res):
    """
    Choosing a color depending on a value of the decimal change:
    red if x >= +0.05
    cyan if x <= -0.07
    white if -0.07 < x < +0.5
    """
    if res > 0.05:
        return BC_FAIL
    elif res > -0.07:
        return BC_WHITE
    else:
        return BC_CYAN


def find_longest_name(benchmark_list):
    """
    Return the length of the longest benchmark name in a given list of
    benchmark JSON objects
    """
    longest_name = 1
    for bc in benchmark_list:
        if len(bc) > longest_name:
            longest_name = len(bc)
    return longest_name


class View:
    """
    View for MVP
    inputs: 'data' - from Presenter, 'benchmark_names'

    Makes an output in cmd or pdf-file
    """
    def __init__(self, presenter):
        """Constructor"""
        self.presenter = presenter  # Обработчик с данными

    def dates_to_str(self):
        """Return list of strings with dates for output message"""
        header = []
        for i in range(len(self.presenter.model.file_dates)):
            s = self.presenter.model.file_dates[i]
            s += '{:^4}'.format(r'\/')
            header += [s]
        return header

    def output_message(self, is_full):
        """Return an array of strings for output"""
        first_col_width = find_longest_name(self.presenter.benchmark_names)
        first_col_width = max(
            first_col_width,
            len('Benchmark'))

        def get_first_line(names):
            lines = []  # ['benchmark    name.json \/ name.json ...', ...]
            while names:
                line = '\n{:<{}s}'.format('Benchmark',
                                          first_col_width + 7)
                n = 7 if len(names) > 7 else len(names)
                for p in range(n):
                    line += names[p]
                line = line[:-4]
                bar = '{}{:-^38}{}'.format('-' * (first_col_width - 3),
                                           '(Time; CPU)',
                                           '-' * (len(line) - first_col_width - 38))
                lines += [line + '\n' + bar]
                del names[:n - 1]
                if len(names) == 1:
                    del names[:1]
            return lines

        first_line = get_first_line(self.dates_to_str())  # list of strings
        blocks = []

        # Блок анализа - вывод "плохих" и "хороших" бенчмарков
        sum_real_cpu_time = self.presenter.sums

        analysis_block = []
        analysis_block += ['{}{}{endc}'.format(BC_FAIL, '\nWorsened benchmarks:', endc=BC_ENDC)]
        for k in range(len(self.presenter.benchmark_names)):
            if sum_real_cpu_time[k][0] >= 0.05 or sum_real_cpu_time[k][1] >= 0.05:
                analysis_block += [self.presenter.benchmark_names[k]]
        analysis_block += ['{}{}{endc}'.format(BC_CYAN, '\nImproved benchmarks:', endc=BC_ENDC)]
        for k in range(len(self.presenter.benchmark_names)):
            if sum_real_cpu_time[k][0] <= -0.05 or sum_real_cpu_time[k][1] <= -0.05:
                analysis_block += [self.presenter.benchmark_names[k]]

        blocks += [analysis_block]

        # Если был указан --full
        if is_full:
            # выводим таблицу сравнений бенчмарков
            for q in range(len(first_line)):
                message = [first_line[q]]
                for i in range(len(self.presenter.benchmark_names)):
                    time_cpu_res = ''
                    # Чтобы красиво умещалось, помещаем по 6 сравнений в один блок
                    for k in range(6 * q, 6 * (q + 1)):
                        try:
                            time_cpu_res += '{}{:+8f}{endc};{}{:+8f}{endc} |'.format(
                                choose_color(self.presenter.deltas[k][i][0]),
                                self.presenter.deltas[k][i][0],
                                choose_color(self.presenter.deltas[k][i][1]),
                                self.presenter.deltas[k][i][1],
                                endc=BC_ENDC)
                        # Если сравнения не полностью заполняют таблицу - прекращаем вывод, это последний блок
                        except IndexError:
                            break
                    message += ['{}{:<{}}{endc}{}'.format(BC_HEADER,
                                                          self.presenter.benchmark_names[i],
                                                          first_col_width + 6,
                                                          time_cpu_res,
                                                          endc=BC_ENDC)]
                blocks += [message]
        return blocks

    def print_cmd(self, is_full):
        for block in self.output_message(is_full):
            for line in block:
                print(line)

    def create_pdf(self, path, name, sum_real_cpu_time, if_graphs):
        """Creates pdf-file"""
        from fpdf import FPDF

        def h1(text):
            """Makes a header, text-size 22"""
            pdf.set_font("Courier", 'B', size=22)
            pdf.cell(190, 12, txt=text, ln=1, align="C")
            pdf.set_font("Courier", size=11)

        pdf = FPDF()
        pdf.add_page()

        h1("Analysis")

        def print_bench_res(kk, link):
            """Prints sums of benchmarks' t and cpu"""
            pdf.cell(10)
            pdf.cell(100, 5, txt='{}'.format(self.presenter.benchmark_names[kk]), ln=1, link=link)
            pdf.cell(20)
            pdf.cell(100, 5,
                     txt='t = {:+7.4f}; CPU = {:+7.4f}'.format(sum_real_cpu_time[kk][0], sum_real_cpu_time[kk][1]),
                     ln=1, link=link)
            pdf.cell(0, 2, ln=1)

        pdf.set_text_color(r=80, g=0, b=0)
        pdf.cell(100, 10, txt="Benchmarks with worsened performance:", ln=1)
        pdf.set_text_color(r=0)
        links = []
        for k in range(len(self.presenter.benchmark_names)):
            links += [pdf.add_link()]
            if sum_real_cpu_time[k][0] >= 0.05 or sum_real_cpu_time[k][1] >= 0.05:
                print_bench_res(k, links[k])

        pdf.set_text_color(r=0, g=80, b=0)
        pdf.cell(100, 10, txt="Benchmarks with improved performance:", ln=1)
        pdf.set_text_color(r=0)
        for k in range(len(self.presenter.benchmark_names)):
            if sum_real_cpu_time[k][0] <= -0.05 or sum_real_cpu_time[k][1] <= -0.05:
                print_bench_res(k, links[k])

        # Если вывод был full - добавляем графики
        if if_graphs:
            pdf.add_page()
            h1("Graphs")
            for i in range(len(self.presenter.benchmark_names)):
                pdf.image('{}{}{}{}'.format(path, '/fig_', i, '.png'), w=160)
                pdf.set_link(links[i])
                pdf.cell(0, 5, ln=1)

        pdf.output(path + name)

    def print_pdf(self, output_path, if_del, if_graphs):
        """Create output pdf-file in 'output_path/'"""

        if not os.path.exists(output_path):
            os.mkdir(output_path)

        name = 'analysis.pdf'

        # создаем графики для пдф-файла, если --full==True
        # sum_t_cpu - массив сумм для нахождения среди них выходящих за пределы интервала +-0,05
        if if_graphs:
            print('...drawing graphs')
            name = 'full_analysis.pdf'
            sum_t_cpu = self.presenter.sums
            self.create_graphs(output_path)
            print('  Completed drawing graphs')
        else:
            sum_t_cpu = self.presenter.sums

        # чтобы не было конфликта при создании пдф-файла, проверяем есть ли уже такой в папке,
        # если есть - удаляем, для этого сначала проверяем, если надо - даем, права на удаление
        if os.path.exists(output_path + name):
            print(oct(os.stat(output_path)[ST_MODE])[-3:])
            if oct(os.stat(output_path)[ST_MODE])[-3:] != '777':
                os.chmod(output_path, 0o777)
                print(oct(os.stat(output_path)[ST_MODE])[-3:])
                time.sleep(1)
            os.remove(output_path + name)

        # Создаем пдф-файл "full_analysis.pdf"
        print('...creating pdf-file')
        self.create_pdf(output_path, name, sum_t_cpu, if_graphs)
        print('  Completed creating pdf-file')

        # Если надо было удалить графики - удаляем
        if if_del:
            print('...removing png-files')
            for i in range(len(self.presenter.benchmark_names)):
                png_name = '{}{}{}'.format('fig_', i, '.png')
                if os.path.exists(output_path + png_name):
                    os.remove(output_path + png_name)
            print('  Completed removing png-files')

    def create_graphs(self, output_path):
        """Creates graphs for pdf-file"""
        import plotly.graph_objects as go

        # обозначения для оси Х
        x = []
        for c in range(self.presenter.model.get_amount() - 1):
            x += ['{}-{}'.format(self.presenter.model.file_dates[c][:8],
                                 self.presenter.model.file_dates[c + 1][:8])]
        # получаем значения для оси У
        for i in range(len(self.presenter.benchmark_names)):
            # для каждого бенчмарка новые значения
            y_t = []
            y_cpu = []
            y_t_sum = []
            y_cpu_sum = []
            # создаем массивы для значений t и cpu
            for k in range(self.presenter.model.get_amount() - 1):
                y_t += [self.presenter.deltas[k][i][0]]
                y_cpu += [self.presenter.deltas[k][i][1]]
            # находим суммы этих значений
            # (количество сумм равно количеству проверяемых файлов для красоты вывода)
            for a in range(self.presenter.model.get_amount() - 1):
                y_t_sum += [sum(y_t)]
                y_cpu_sum += [sum(y_cpu)]
            # рисуем графики
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=x, y=y_t,
                                     mode='lines+markers',
                                     line=dict(color='royalblue'),
                                     name='Time'))
            fig.add_trace(go.Scatter(x=x, y=y_cpu,
                                     mode='lines+markers',
                                     line=dict(color='firebrick'),
                                     name='CPU'))
            fig.add_trace(go.Scatter(x=x, y=y_t_sum,
                                     mode='lines',
                                     line=dict(color='royalblue', dash='dot'),
                                     name='sum(Time)'))
            fig.add_trace(go.Scatter(x=x, y=y_cpu_sum,
                                     mode='lines',
                                     line=dict(color='firebrick', dash='dot'),
                                     name='sum(CPU)'))
            fig.update_layout(title='{}'.format(self.presenter.benchmark_names[i]),
                              xaxis_title='Results',
                              yaxis_title='Comparison')
            fig.write_image('{}{}{}{}'.format(output_path, 'fig_', i, '.png'))


# Приводим путь к нормальному виду
def normalize_path(path):
    """Return normalized path string"""
    while path.startswith(' '):
        path = path[1:]
    if not path.endswith('/'):
        path = path + '/'
    return path


def create_parser():
    """
    Create parser for input

    benchmark_reports.py
    path - input path to benchmark-reports' folder
    cmd - output in command line
        -f, --full - full output
        -a, --analysis - analysis output
    pdf - output in pdf-file
        output_path - path for output pdf-file
        -f, --full - full output
        -a, --analysis - analysis output
        -d, --delete_png - delete all graph files
    """
    parser = argparse.ArgumentParser(
        description='compare tool for more than 2 benchmark outputs')
    parser.add_argument(
        'path',  # ./results/
        help="Path to benchmark-reports' folder",
        type=str
    )

    subparsers = parser.add_subparsers(
        help='Choose an output',
        dest='mode'
    )

    cmd_parser = subparsers.add_parser(
        'cmd',
        help='Program writes report in cmd'
    )
    cmd_group = cmd_parser.add_mutually_exclusive_group(required=True)
    cmd_group.add_argument(
        '-f',
        '--full',
        help='Writes out a full comparison table with results of analysis',
        action='store_true',
        dest='full'
    )
    cmd_group.add_argument(
        '-a',
        '--analysis',
        help='Writes out results of analysis',
        action='store_true',
        dest='analysis'
    )

    pdf_parser = subparsers.add_parser(
        'pdf',
        help='Program writes report in pdf-file, saves it in a specified path'
    )
    pdf_parser.add_argument(
        'output_path',
        help='Path for output pdf-file',
        type=str
    )
    pdf_group = pdf_parser.add_mutually_exclusive_group(required=True)
    pdf_group.add_argument(
        '-f',
        '--full',
        help='Writes out a full comparison table and results of analysis',
        action='store_true',
        dest='full'
    )
    pdf_group.add_argument(
        '-a',
        '--analysis',
        help='Writes out results of analysis',
        action='store_true',
        dest='analysis'
    )
    pdf_parser.add_argument(
        '-d',
        '--delete_png',
        help='Deletes pictures with graphs',
        action='store_true',
        dest='d'
    )

    return parser


def main():
    # Take input from user
    # Ввод директории с бенчмарками, метода вывода, пути сохранения для пдф-файла
    # (ex: c:/moex/benchmark_reports/results/ pdf c:/moex/benchmark_reports/output -f -d)
    parser = create_parser()
    args = parser.parse_args()

    print('Program started')

    if args.mode is None:
        parser.print_help()
        exit(1)

    files = Model(normalize_path(args.path))
    files.get_data()

    if files.get_amount() < 2:
        parser.print_help()
        exit(2)

    processing = Presenter(files)
    processing.compare()
    showing = View(processing)

    if args.mode == 'cmd':
        showing.print_cmd(args.full)
    elif args.mode == 'pdf':
        showing.print_pdf(normalize_path(args.output_path), args.d, args.full)

    print('Program ended')


if __name__ == '__main__':
    main()

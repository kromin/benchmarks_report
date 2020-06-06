import inspect

import numpy
import os
import sys
import argparse
from subprocess import Popen, PIPE
from tools.gbench import report

# Opening subfolder tools
# Открываем подпапку tools
cmd_subfolder = os.path.realpath(
    os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "tools")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)


class Model:
    """
    Model for MVP
    input: 'path', '.extension'

    Find files, collects their names and their amount in specified path
    """

    def __init__(self, path, extension='.json'):
        """Constructor creates variables 'names' and 'extension'"""
        self.filenames = []
        for file in os.listdir(path):
            if file.endswith(extension):
                self.filenames.append(file)
        self.path = path
        self.extension = extension

    def get_amount(self):
        """Get quantity of json files"""
        return len(self.filenames)


class Presenter:
    """
    Presenter for MVP
    input: 'data' - from Model

    Compares and analyses benchmark data inside
    """

    def __init__(self, model):
        """Constructor"""
        self.model = model  # экземпляр класса Модель
        self.benchmark_names = []  # список названий бенчмарков
        self.delta_in_file = []  # список чисел отклонений
        self.lines_in_file = []  # список массивов номеров строк отклонений
        self.err = ''  # возможная ошибка при прочтении файлов

    def compare_pair(self, file1, file2):
        """Compare two files using Google Benchmark compare.py script and return output string and error, if occurs"""
        print('Comparing {0} to {1}'.format(file1, file2))
        path_to_current_folder = os.path.dirname(os.path.realpath(__file__))
        process = Popen(
            ['python', path_to_current_folder + '/tools/compare.py', 'benchmarks',
             self.model.path + file1,
             self.model.path + file2],
            stdout=PIPE, stderr=PIPE, universal_newlines=True
        )
        (output, err) = process.communicate()
        return output, err

    def lines_output(self, output):
        """Return array of lines for beatified output"""
        while output:
            if output.startswith('Portf'):
                self.benchmark_names.append(output[:64])  # 43
                output = output[1:]
            elif output.startswith('Match'):
                self.benchmark_names.append(output[:64])  # 61
                output = output[1:]
            elif output.startswith('Misc'):
                self.benchmark_names.append(output[:64])  # 34
                output = output[1:]
            else:
                output = output[1:]
        return self.benchmark_names

    # Создаем массив с левым и правым столбцами дельт
    @staticmethod
    def get_lr_nums(nums):
        """Return an array with 2 columns out of line"""
        n = len(nums)
        lr_nums = numpy.zeros((int(n / 2), 2))
        j = 0
        for i in range(n):
            if i % 2 == 0:
                lr_nums[j][0] = nums[i]
            else:
                lr_nums[j][1] = nums[i]
                j += 1
        return lr_nums

    # Находим числа отклонений вида х.хххх со знаками + или - перед ними и помещаем в массив
    def find_nums(self, output_string):
        """
        Find numbers (deviations) of a kind +x.xxxx or -x.xxxx
        and return array of these numbers
        """
        nums = []
        temp_string = output_string
        while temp_string:
            if temp_string.startswith('+'):
                temp_string = temp_string[1:]
                try:
                    nums.append(float(temp_string[:6]))
                except ValueError:
                    pass
            elif temp_string.startswith('-0'):
                temp_string = temp_string[1:]
                try:
                    nums.append(-1 * float(temp_string[:6]))
                except ValueError:
                    pass
            else:
                temp_string = temp_string[1:]
        lr_nums = self.get_lr_nums(nums)
        return lr_nums

    # Находим отклонение на величину >= 0.05
    @staticmethod
    def find_large_deviation(nums):
        """Find deviation greater than 0.5 and return array of line indexes"""
        n = len(nums)
        indexes = numpy.zeros((n, 2))

        # Находим отклонения большие 0.05 и помещаем номера строк в массив (начало отсчета с первых цифр)
        # Если отклонение положительно, то номер строки положителен, и наоборот
        j = 0
        for i in range(n):
            flag = False
            if nums[i][0] >= 0.05:
                indexes[j][0] = i
                flag = True
            if nums[i][1] >= 0.05:
                indexes[j][1] = i
                flag = True
            if nums[i][0] <= -0.05:
                indexes[j][0] = -1 * i
                flag = True
            if nums[i][1] <= -0.05:
                indexes[j][1] = -1 * i
                flag = True
            if flag:
                j += 1
        indexes = numpy.delete(indexes, slice(j, n), 0)
        return indexes

    def compare_all(self):
        """
        Compare all files in directory and return list of arrays containing deviations greater than 0.5,
        text for beautified output and list of arrays containing # of lines of deviations in file
        """

        for i in range(1, self.model.get_amount()):
            # Compare files in pairs
            # Сравниваем файлы попарно
            output, self.err = self.compare_pair(self.model.filenames[i - 1], self.model.filenames[i])

            # print(output)
            # Make lines for beautified output
            # Создаем строки для красивого вывода
            if i == 1:
                self.lines_output(output)

            # Find numbers of deviations in output, put them into list
            # Находим числа отклонений, кладем в список в виде
            nums_output = self.find_nums(output)
            self.delta_in_file.append(nums_output)

            # Get array of line numbers of deviations greater than 0.5
            # Получаем массив номеров строк отклонений, больших чем 0,5
            line_number = self.find_large_deviation(nums_output)

            # Put array into list
            # Кладем массив в список
            self.lines_in_file.append(line_number)
        return self.lines_in_file, self.err, self.delta_in_file


BC_NONE = report.BC_NONE
BC_MAGENTA = report.BC_MAGENTA
BC_CYAN = report.BC_CYAN
BC_OKBLUE = report.BC_OKBLUE
BC_OKGREEN = report.BC_OKGREEN
BC_HEADER = report.BC_HEADER
BC_WARNING = report.BC_WARNING
BC_WHITE = report.BC_WHITE
BC_FAIL = report.BC_FAIL
BC_ENDC = report.BC_ENDC
BC_BOLD = report.BC_BOLD
BC_UNDERLINE = report.BC_UNDERLINE


def find_longest_name(benchmark_names):
    first_col_width = 1
    for k in range(len(benchmark_names)):
        if first_col_width < len(benchmark_names[k]):
            first_col_width = len(benchmark_names[k])
    return first_col_width


class View:
    """
    View for MVP
    inputs: 'data' - from Presenter, 'benchmark_names'

    Makes an output in cmd or pdf-file
    """

    def __init__(self, presenter):
        """Constructor"""
        self.presenter = presenter  # Обработчик с данными

    def names_to_str(self):
        """Return list of strings with filenames for output message"""
        header = []
        for i in range(len(self.presenter.model.filenames)):
            s = self.presenter.model.filenames[i][:11]
            # if i != len(self.presenter.model.filenames) - 1:
            s += '{:^8}'.format(r'\/')
            header += [s]
        return header

    def more_zeros(self, lines):
        """Return an array with added 0.0 where needed"""
        n = len(self.presenter.benchmark_names)
        double = numpy.zeros((n, 2))
        for i in range(1, n):
            for k in range(len(lines)):
                if i == abs(lines[k][0]) or i == abs(lines[k][1]):
                    if lines[k][0] != 0 or lines[k][1] != 0:
                        double[i][0] = lines[k][0]
                        double[i][1] = lines[k][1]
        return double

    @staticmethod
    def time_cpu_is_improved(time, cpu):
        """Return if Time and CPU values improved/worsened/within error"""
        time_is_improved = 0
        cpu_is_improved = 0
        if time != 0 and cpu != 0:  # if both != 0
            # number = time
            if time > 0:  # if time is worsened
                if cpu < 0:  # if cpu is improved
                    cpu_is_improved = 1
            else:  # if time is improved
                time_is_improved = 1
                if cpu < 0:  # if cpu is improved
                    cpu_is_improved = 1
        elif time != 0:  # if cpu is within error
            # number = time
            cpu_is_improved = -1
            if time < 0:  # if time is improved
                time_is_improved = 1
        elif cpu != 0:  # if time is within error
            # number = cpu
            time_is_improved = -1
            if cpu < 0:  # if cpu is improved
                cpu_is_improved = 1
        else:
            # number = 0
            time_is_improved = -1
            cpu_is_improved = -1
        return time_is_improved, cpu_is_improved

    @staticmethod
    def choose_color(is_improved, delta):
        """Return a colored string with a value for output message"""
        if is_improved == 1:
            color = BC_CYAN
        elif is_improved == 0:
            color = BC_FAIL
        else:
            color = BC_NONE
        string = '{}{:+8.4f}'.format(
            color,
            delta
        )
        return string

    def find_sum_t_cpu(self):
        sum_t_cpu = []
        for i in range(len(self.presenter.benchmark_names)):
            sum_t_cpu.append([])
            sum_t = 0
            sum_cpu = 0
            for k in range(self.presenter.model.get_amount() - 1):
                sum_t += self.presenter.delta_in_file[k].item(i, 0)
                sum_cpu += self.presenter.delta_in_file[k].item(i, 1)
            sum_t_cpu[i] = [sum_t, sum_cpu]
        return sum_t_cpu

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
                                          first_col_width)
                n = 7 if len(names) > 7 else len(names)
                for p in range(n):
                    line += names[p]
                bar = '{}{:-^17}{}'.format('-' * (first_col_width + 6),
                                           '(Time; CPU)',
                                           '-' * (len(line) - first_col_width - 32))
                lines += [line[:-8] + '\n' + bar]
                del names[:n - 1]
                if len(names) == 1:
                    del names[:1]
            return lines

        first_line = get_first_line(self.names_to_str())  # list of strings
        blocks = []

        # Блок анализа - вывод "плохих" и "хороших" бенчмарков
        sum_t_cpu = self.find_sum_t_cpu()
        analysis_block = []
        analysis_block += ['{}{}{endc}'.format(BC_FAIL, '\nWorsened benchmarks:', endc=BC_ENDC)]
        for k in range(len(self.presenter.benchmark_names)):
            if sum_t_cpu[k][0] >= 0.05 or sum_t_cpu[k][1] >= 0.05:
                analysis_block += [self.presenter.benchmark_names[k]]
        analysis_block += ['{}{}{endc}'.format(BC_CYAN, '\nImproved benchmarks:', endc=BC_ENDC)]
        for k in range(len(self.presenter.benchmark_names)):
            if sum_t_cpu[k][0] <= -0.05 or sum_t_cpu[k][1] <= -0.05:
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
                            full_lines = self.more_zeros(self.presenter.lines_in_file[k])
                            time = full_lines[i][0]
                            cpu = full_lines[i][1]
                            time_is_improved, cpu_is_improved = self.time_cpu_is_improved(time, cpu)
                            delta_0 = self.presenter.delta_in_file[k].item(i, 0)
                            delta_1 = self.presenter.delta_in_file[k].item(i, 1)

                            time_cpu_res += '{:8}{endc};{:8}{endc} |'.format(self.choose_color(time_is_improved, delta_0),
                                                                             self.choose_color(cpu_is_improved, delta_1),
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
        """Print full output in command line"""
        if self.presenter.err:
            print('{}{:>11s}{}{endc}'.format(BC_FAIL,
                                             'err::: ',
                                             self.presenter.err,
                                             endc=BC_ENDC
                                             ))

        for block in self.output_message(is_full):
            for line in block:
                print(line)

    def print_cmd_a(self):
        """Print analysis output in command line"""
        pass

    def create_graphs(self, path):
        """Creates graphs for pdf-file"""
        import plotly.graph_objects as go

        x = []
        sum_t_cpu = []

        # обозначения для оси Х
        for c in range(len(self.presenter.model.filenames) - 1):
            x += ['{}-{}'.format(self.presenter.model.filenames[c][7:11],
                                 self.presenter.model.filenames[c + 1][7:11])]
        # получаем значения для оси У
        for i in range(len(self.presenter.benchmark_names)):
            # для каждого бенчмарка новые значения
            y_t = []
            y_cpu = []
            y_t_sum = []
            y_cpu_sum = []
            # создаем массивы для значений t и cpu
            for k in range(self.presenter.model.get_amount() - 1):
                y_t += [self.presenter.delta_in_file[k].item(i, 0)]
                y_cpu += [self.presenter.delta_in_file[k].item(i, 1)]
            # находим суммы этих значений
            # (количество сумм равно количеству проверяемых файлов для красоты вывода)
            for a in range(self.presenter.model.get_amount() - 1):
                y_t_sum += [numpy.sum(y_t)]
                y_cpu_sum += [numpy.sum(y_cpu)]
                # создаем массив сумм для их дальнейшей обработки
                if a == 0:
                    sum_t_cpu.append([y_t_sum[0], y_cpu_sum[0]])
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
            fig.write_image('{}{}{}{}'.format(path, '/fig_', i, '.png'))
        return sum_t_cpu

    def create_pdf(self, path, name, sum_t_cpu, if_graphs):
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
                     txt='t = {:+7.4f}; CPU = {:+7.4f}'.format(sum_t_cpu[kk][0], sum_t_cpu[kk][1]),
                     ln=1, link=link)
            pdf.cell(0, 2, ln=1)

        pdf.set_text_color(r=80, g=0, b=0)
        pdf.cell(100, 10, txt="Benchmarks with worsened performance:", ln=1)
        pdf.set_text_color(r=0)
        links = []
        for k in range(len(self.presenter.benchmark_names)):
            links += [pdf.add_link()]
            if sum_t_cpu[k][0] >= 0.05 or sum_t_cpu[k][1] >= 0.05:
                print_bench_res(k, links[k])

        pdf.set_text_color(r=0, g=80, b=0)
        pdf.cell(100, 10, txt="Benchmarks with improved performance:", ln=1)
        pdf.set_text_color(r=0)
        for k in range(len(self.presenter.benchmark_names)):
            if sum_t_cpu[k][0] <= -0.05 or sum_t_cpu[k][1] <= -0.05:
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

    def print_pdf(self, path, if_del, if_graphs):
        """Create full output in 'path/full.pdf' pdf-file"""

        if not os.path.exists(path):
            os.mkdir(path)

        name = '/analysis.pdf'

        # создаем графики для пдф-файла, если --full==True
        # sum_t_cpu - массив сумм для нахождения среди них выходящих за пределы интервала +-0,05
        if if_graphs:
            print('...drawing graphs')
            name = '/full.pdf'
            sum_t_cpu = self.create_graphs(path)
            print('Completed drawing graphs')
        else:
            sum_t_cpu = self.find_sum_t_cpu()

        # чтобы не было конфликта при создании пдф-файла, проверяем есть ли уже такой в папке,
        # если есть - удаляем, для этого сначала даем права на удаление
        if os.path.exists(path + name):
            os.chmod(path + name, 0o777)
            os.remove(path + name)

        # Создаем пдф-файл "full.pdf"
        print('...creating pdf-file')
        self.create_pdf(path, name, sum_t_cpu, if_graphs)
        print('Completed creating pdf-file')

        # Если надо было удалить графики - удаляем
        if if_del:
            print('...removing png-files')
            for i in range(len(self.presenter.benchmark_names)):
                png_name = '{}{}{}'.format('/fig_', i, '.png')
                if os.path.exists(path + png_name):
                    os.remove(path + png_name)
            print('Completed removing png-files')


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

    compare_1000.py
    path - input path to benchmark-reports' folder
    cmd - output in command line
        -f, --full - full output

    not supported yet:
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
        help='Deletes graph pictures',
        action='store_true',
        dest='d'
    )

    return parser


def main():
    # Take input from user
    # Ввод директории с бенчмарками, метода вывода, пути сохранения для пдф-файла
    # (ex: c:/MOEX/results/ pdf c:/moex/mvp_comp/output)
    parser = create_parser()
    args = parser.parse_args()

    if args.mode is None:
        parser.print_help()
        exit(1)

    files = Model(normalize_path(args.path))

    if files.get_amount() < 2:
        parser.print_help()
        exit(2)

    processing = Presenter(files)
    processing.compare_all()
    showing = View(processing)

    if args.mode == 'cmd':
        showing.print_cmd(args.full)
    elif args.mode == 'pdf':
        showing.print_pdf(args.output_path, args.d, args.full)


if __name__ == '__main__':
    main()

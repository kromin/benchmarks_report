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
        are_lines_output_made = False

        for i in range(1, len(self.model.filenames)):
            # Compare files in pairs
            # Сравниваем файлы попарно
            output, self.err = self.compare_pair(self.model.filenames[i - 1], self.model.filenames[i])

            # print(output)
            # Make lines for beautified output
            # Создаем строки для красивого вывода
            if not are_lines_output_made:
                self.lines_output(output)
                are_lines_output_made = True

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
        """Return string out of filename-list for output message"""
        s = ''
        for i in range(len(self.presenter.model.filenames)):
            s += self.presenter.model.filenames[i][:11]
            if i != len(self.presenter.model.filenames) - 1:
                s += '{:^8}'.format(r'\/')
        return s

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

    def output_message(self):
        """Return an array of strings for output"""
        first_col_width = find_longest_name(self.presenter.benchmark_names)
        first_col_width = max(
            first_col_width,
            len('Benchmark'))

        first_line = '\n{:<{}s}{}'.format('Benchmark',
                                          first_col_width,
                                          self.names_to_str())
        bar = '{:-<{}s}{:-^17}{:-<{}s}'.format('',
                                               first_col_width + 6,
                                               '(Time; CPU)',
                                               '',
                                               len(first_line) - first_col_width - 24
                                               )
        message = [first_line, bar]

        for i in range(len(self.presenter.benchmark_names)):
            time_cpu_res = ''
            for k in range(len(self.presenter.model.filenames) - 1):
                full_lines = self.more_zeros(self.presenter.lines_in_file[k])
                time = full_lines[i][0]
                cpu = full_lines[i][1]
                time_is_improved, cpu_is_improved = self.time_cpu_is_improved(time, cpu)
                delta_0 = self.presenter.delta_in_file[k].item(i, 0)
                delta_1 = self.presenter.delta_in_file[k].item(i, 1)
                time_cpu_res += '{:8}{endc};{:8}{endc} |'.format(self.choose_color(time_is_improved, delta_0),
                                                                 self.choose_color(cpu_is_improved, delta_1),
                                                                 endc=BC_ENDC)
            message += ['{}{:<{}}{endc}{}'.format(BC_HEADER,
                                                  self.presenter.benchmark_names[i],
                                                  first_col_width + 6,
                                                  time_cpu_res,
                                                  endc=BC_ENDC)]
        return message

    def print_cmd_f(self):
        """Print full output in command line"""
        self.presenter.compare_all()

        if self.presenter.err:
            print('    err:::', self.presenter.err)

        for line in self.output_message():
            print(line)

        # if len(self.presenter.model.filenames) < 9:
        #
        # else:
        #     pass
        # if len(self.presenter.model.filenames) < 3:
        #     self.output_message_for_two()
        # elif 3 <= len(self.presenter.model.filenames) < 7:
        #     self.output_message_for_many()
        # else:
        #     while self.presenter.model.filenames:
        #         output_message_for_many(lines_in_file[:6], lines_out, filenames[:6], delta_in_file[:6])
        #         del lines_in_file[:5]
        #         del filenames[:5]
        #         del delta_in_file[:5]

    def print_cmd_a(self):
        """Print analysis output in command line"""
        pass

    def print_pdf_f(self):
        """Print full output in pdf-file"""
        return ''

    def print_pdf_a(self):
        """Print analysis output in pdf-file"""
        return ''


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
        output - direct the output to a name of your choice
        -f, --full - full output
        -a, --analysis - analysis output
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
        'output',
        help='Directs the output to a name of your choice',
        type=str
    )
    pdf_group = pdf_parser.add_mutually_exclusive_group(required=True)
    pdf_group.add_argument(
        '-f',
        '--full',
        help='Writes out a full comparison table with results of analysis',
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
    processing = Presenter(files)
    showing = View(processing)

    if args.mode == 'cmd':
        if args.full:
            showing.print_cmd_f()
        elif args.analysis:
            showing.print_cmd_a()
    elif args.mode == 'pdf':
        with open(args.output, 'w') as output_file:
            if args.f:
                output_file.write(showing.print_pdf_f())
            elif args.a:
                output_file.write(showing.print_pdf_a())
        output_file.close()


if __name__ == '__main__':
    main()

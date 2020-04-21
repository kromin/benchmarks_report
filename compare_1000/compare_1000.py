import inspect
import numpy
import os
import sys
import argparse
from subprocess import Popen, PIPE

# Opening subfolder tools
# Открываем подпапку tools
cmd_subfolder = os.path.realpath(
    os.path.abspath(os.path.join(os.path.split(inspect.getfile(inspect.currentframe()))[0], "tools")))
if cmd_subfolder not in sys.path:
    sys.path.insert(0, cmd_subfolder)


# Получаем все имена .JSON в папке
def get_json_filenames(path):
    """Get names ending with .json in path and return list of names"""
    names = []
    for file in os.listdir(path):
        if file.endswith(".json"):
            names.append(file)
    return names


# Используя скрипт Google Benchmark compare.py проверяем два файла
def compare_pair(file1, file2, path):
    """Compare two files using Google Benchmark compare.py script and return output string and error, if occurs"""
    path_to_current_folder = os.path.dirname(os.path.realpath(__file__))
    process = Popen(
        ['python', path_to_current_folder + '/tools/compare.py', 'benchmarks',
         path + file1,
         path + file2],
        stdout=PIPE, stderr=PIPE, universal_newlines=True
    )
    (output, err) = process.communicate()
    return output, err


# Создаем массив с левым и правым столбцами дельт
def get_lr_mums(nums):
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
def find_nums(output_string):
    """Find numbers (deviations) of a kind +x.xxxx or -x.xxxx and return array of these numbers"""
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
    lr_nums = get_lr_mums(nums)
    return lr_nums


# Находим отклонение на величину >= 0.05
def find_large_deviation(lr_nums):
    """Find deviation greater than 0.5 and return array of line indexes"""
    n = len(lr_nums)
    indexes = numpy.zeros((n, 2))

    # Находим отклонения большие 0.05 и помещаем номера строк в массив (начало отсчета с первых цифр)
    # Если отклонение положительно, то номер строки положителен, и наоборот
    j = 0
    for i in range(n):
        flag = False
        if lr_nums[i][0] >= 0.05:
            indexes[j][0] = i
            flag = True
        if lr_nums[i][1] >= 0.05:
            indexes[j][1] = i
            flag = True
        if lr_nums[i][0] <= -0.05:
            indexes[j][0] = -1 * i
            flag = True
        if lr_nums[i][1] <= -0.05:
            indexes[j][1] = -1 * i
            flag = True
        if flag:
            j += 1
    indexes = numpy.delete(indexes, slice(j, n), 0)
    return indexes


# Попарная проверка всех файлов в директории
def compare_all(path, names):
    """Compare all files in directory and return list of arrays containing deviations greater than 0.5,
    text for beautified output and list of arrays containing # of lines of deviations in file"""
    lines_in_file = []
    delta_in_file = []
    lines_out = []
    err = ''
    are_lines_output_made = False
    for i in range(1, len(names)):
        # Compare files in pairs
        # Сравниваем файлы попарно
        output, err = compare_pair(names[i - 1], names[i], path)

        print('Comparing {0} to {1}'.format(names[i - 1], names[i]))
        # print(output)
        # Make lines for beautified output
        # Создаем строки для красивого вывода
        if not are_lines_output_made:
            lines_out = lines_output(output)
            are_lines_output_made = True

        # Find numbers of deviations in output, put them into list
        # Находим числа отклонений, кладем в список
        nums_output = find_nums(output)
        delta_in_file.append(nums_output)

        # Get array of line numbers of deviations greater than 0.5
        # Получаем массив номеров строк отклонений, больших чем 0,5
        line_number = find_large_deviation(nums_output)

        # Put array into list
        # Кладем массив в список
        lines_in_file.append(line_number)
    return lines_in_file, err, lines_out, delta_in_file


# Приводим путь к нормальному виду
def normalize_path(path):
    """Return normalized path string"""
    while path.startswith(' '):
        path = path[1:]
    if not path.endswith('/'):
        path = path + '/'
    return path


# Возвращаем строки с названиями бенчмарков
def lines_output(output):
    """Return array of lines for beatified output"""
    lines = []
    while output:
        if output.startswith('Portf'):
            lines.append(output[:64])  # 43
            output = output[1:]
        elif output.startswith('Match'):
            lines.append(output[:64])  # 61
            output = output[1:]
        elif output.startswith('Misc'):
            lines.append(output[:64])  # 34
            output = output[1:]
        else:
            output = output[1:]
    return lines


# Класс для форматирования вывода в командную строку
class CMDFormat:
    """Class for color codes used in CMD"""
    CEND = '\33[0m'
    CWAVEBLUE = '\33[36;1m'
    CLIGHTGREEN = '\33[32;1m'
    CSTRONGRED = '\33[31;1m'
    CGRAY = '\33[37m'
    CWHITE = '\33[37;1m'
    SPACE = '        '
    LINE = '--------'


# Функция вывода текста нужного цвета
def print_for_two(benchmark_name, filename, time_is_improved, delta_0, cpu_is_improved, delta_1):
    delta_0 = str(delta_0)
    delta_1 = str(delta_1)
    if time_is_improved == 1:
        time_str = CMDFormat.CWAVEBLUE + 'improved by  ' + delta_0 + CMDFormat.CEND
    elif time_is_improved == 0:
        time_str = CMDFormat.CSTRONGRED + 'worsened by  ' + delta_0 + CMDFormat.CEND
    else:
        time_str = CMDFormat.CGRAY + 'within error ' + delta_0 + CMDFormat.CEND
    if cpu_is_improved == 1:
        cpu_str = CMDFormat.CWAVEBLUE + 'improved by  ' + delta_1 + CMDFormat.CEND
    elif cpu_is_improved == 0:
        cpu_str = CMDFormat.CSTRONGRED + 'worsened by  ' + delta_1 + CMDFormat.CEND
    else:
        cpu_str = CMDFormat.CGRAY + 'within error ' + delta_1 + CMDFormat.CEND
    print(CMDFormat.CLIGHTGREEN + benchmark_name + CMDFormat.CEND + '{0}  "Time" {1}; "CPU" {2}'.format(
        filename,
        time_str,
        cpu_str))


# Проверка, улучшились/ухудшились/не изменились ли показатели time и cpu
def time_cpu_is_improved(time, cpu):
    """Return number of line that has anything but 0.0 and flags for states of Time and CPU values"""
    time_is_improved = 0
    cpu_is_improved = 0
    if time != 0 and cpu != 0:  # if both != 0
        number = time
        if time > 0:  # if time is worsened
            if cpu < 0:  # if cpu is improved
                cpu_is_improved = 1
        else:  # if time is improved
            time_is_improved = 1
            if cpu < 0:  # if cpu is improved
                cpu_is_improved = 1
    elif time != 0:  # if cpu is within error
        number = time
        cpu_is_improved = -1
        if time < 0:  # if time is improved
            time_is_improved = 1
    elif cpu != 0:  # if time is within error
        number = cpu
        time_is_improved = -1
        if cpu < 0:  # if cpu is improved
            cpu_is_improved = 1
    else:
        number = 0
        time_is_improved = -1
        cpu_is_improved = -1
    return abs(number), time_is_improved, cpu_is_improved


# Красивый вывод
def output_message_for_two(lines_in_file, lines_out, filename, delta_in_file):
    """Print beautified output when only 2 files were compared"""
    for i in range(1, len(filename)):
        print("\nResults of comparison between {0} and {1}: ".format(filename[i - 1], filename[i]) + "\n")
        print(
            CMDFormat.CWHITE
            + 'Benchmark      {0} Filename {1} Changes from prev version'.format(
                CMDFormat.SPACE * 6,
                CMDFormat.SPACE)
            + CMDFormat.CEND)
        print(CMDFormat.LINE * 17)
        j = i - 1
        for k in range(len(lines_in_file[j])):
            time = int(lines_in_file[j].item((k, 0)))
            cpu = int(lines_in_file[j].item((k, 1)))
            number, time_is_improved, cpu_is_improved = time_cpu_is_improved(time, cpu)
            delta_0 = abs(delta_in_file[j].item(abs(number), 0))
            delta_1 = abs(delta_in_file[j].item(abs(number), 1))
            print_for_two(
                lines_out[number],
                filename[i],
                time_is_improved,
                delta_0,
                cpu_is_improved,
                delta_1)


def names_to_str(filename):
    """Return string out of filename-list for output message"""
    s = '(Time; CPU) |  '
    for i in range(len(filename)):
        s = s + filename[i][:11]
        if i != len(filename) - 1:
            s = s + r'   \/   '
    return s


def more_zeros(lines, n):
    """Return an array with added 0.0 where needed"""
    double = numpy.zeros((n, 2))
    for i in range(1, n):
        for k in range(len(lines)):
            if i == abs(lines[k][0]) or i == abs(lines[k][1]):
                if lines[k][0] != 0 or lines[k][1] != 0:
                    double[i][0] = lines[k][0]
                    double[i][1] = lines[k][1]
    return double


def optimise_string(delta):
    """Return pretty string for output message"""
    if len(delta) != 7 and delta.startswith('-'):
        delta = delta + '0' * (7 - len(delta))
    elif len(delta) != 7:
        delta = ' ' + delta + '0' * (6 - len(delta))
    return delta


def choose_color(is_improved, delta):
    """Return a colored string with a value for output message"""
    if is_improved == 1:
        string = CMDFormat.CWAVEBLUE + delta + CMDFormat.CEND
    elif is_improved == 0:
        string = CMDFormat.CSTRONGRED + delta + CMDFormat.CEND
    else:
        string = CMDFormat.CGRAY + delta + CMDFormat.CEND
    return string


def output_message_for_many(lines_in_file, lines_out, filename, delta_in_file):
    """Print output in table format for more than 2 compared files"""
    print(CMDFormat.CWHITE + '\nBenchmark' + ' ' * 42 + names_to_str(filename) + CMDFormat.CEND)
    print(CMDFormat.LINE * 20)
    for i in range(len(lines_out)):  # from 0 to 54
        out_string = ''
        for k in range(len(filename) - 1):
            full_lines = more_zeros(lines_in_file[k], len(lines_out))
            time = full_lines[i][0]
            cpu = full_lines[i][1]
            number, time_is_improved, cpu_is_improved = time_cpu_is_improved(time, cpu)
            delta_0 = optimise_string(str(delta_in_file[k].item(i, 0)))
            delta_1 = optimise_string(str(delta_in_file[k].item(i, 1)))
            if number != 0:
                time_str = choose_color(time_is_improved, delta_0)
                cpu_str = choose_color(cpu_is_improved, delta_1)
            else:
                time_str = CMDFormat.CGRAY + delta_0 + CMDFormat.CEND
                cpu_str = CMDFormat.CGRAY + delta_1 + CMDFormat.CEND
            out_string = out_string + time_str + '; ' + cpu_str + ' | '
        print(CMDFormat.CLIGHTGREEN + lines_out[i] + CMDFormat.CEND + ' ' * 9 + out_string)


def graphs():
    """Draw graphs for 2 (or more) versions"""
    return 0


def main():
    # Take input from user
    # Ввод директории с бенчмарками
    # (ex: c:/users/trusovii/desktop/results/, c:/users/admin/desktop/MOEX/results/)
    parser = argparse.ArgumentParser(
        description='compare tool for more than 2 benchmark outputs')
    parser.add_argument(
        'path',  # ./results/
        help="path to benchmark-reports' folder",
    )
    args = parser.parse_args()

    print("In progress\n")

    # print("Enter full pathname of the benchmark-reports' folder")
    path_to_benchmarks = normalize_path(args.path)
    filenames = get_json_filenames(path_to_benchmarks)

    # Get list of arrays of line numbers with deviations greater than 0.5
    # Получаем список из массивов номеров строк с отклонениями > 0.5, строки для вывода и
    lines_in_file, err, lines_out, delta_in_file = compare_all(path_to_benchmarks, filenames)

    if err:
        print('    err:::', err)
    if len(filenames) < 3:
        output_message_for_two(lines_in_file, lines_out, filenames, delta_in_file)
    elif 3 <= len(filenames) < 7:
        output_message_for_many(lines_in_file, lines_out, filenames, delta_in_file)
    else:
        while filenames:
            output_message_for_many(lines_in_file[:6], lines_out, filenames[:6], delta_in_file[:6])
            del lines_in_file[:5]
            del filenames[:5]
            del delta_in_file[:5]

    # TODO: Улучшить вывод программы:
    #      * График для двух (и более) версий, учитывая все значения


if __name__ == '__main__':
    # unittest.main()
    main()

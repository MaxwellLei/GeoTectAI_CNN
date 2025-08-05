import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import seaborn as sns
import numpy as np
import re
import os
from sklearn.preprocessing import MinMaxScaler, QuantileTransformer
from sklearn.model_selection import train_test_split
import shutil
import pyarrow.parquet as pq
import pyarrow as pa
from PIL import Image
from tqdm import tqdm
import concurrent.futures


# 挑选完整数据集-威胁方法，执行之前确保数据备份了
def process_dataset(dataset_path, excel_file):
    # 读取Excel文件
    df = pd.read_excel(excel_file)

    # 遍历数据集文件夹
    for category in os.listdir(dataset_path):
        category_path = os.path.join(dataset_path, category)
        if os.path.isdir(category_path):
            # 获取对应类别的数值列
            if category in df.columns:
                valid_values = set(df[category].dropna().astype(int).astype(str))

                # 遍历类别文件夹中的样本
                for sample in os.listdir(category_path):
                    # 移除文件扩展名并获取最后的数字
                    sample_name = os.path.splitext(sample)[0]
                    sample_id = sample_name.split('_')[-1]

                    if sample_id not in valid_values:
                        # 如果样本ID不在有效值列表中,删除该样本
                        sample_path = os.path.join(category_path, sample)
                        os.remove(sample_path)
                        print(f"Removed: {sample_path}")
            else:
                print(f"Warning: Category '{category}' not found in Excel file.")

# 统计合并类别平均样本
def cal_img(df_r, df_g, df_b, w, h, output_folder):
    # 确保三个数据框的形状相同
    assert df_r.shape == df_g.shape == df_b.shape, "数据框的形状不一致"

    # 获取类别标签
    labels = df_r.iloc[:, 0].unique()

    # 为每个类别计算平均值
    for label in labels:
        # 获取当前类别的数据
        r_data = df_r[df_r.iloc[:, 0] == label].iloc[:, 1:86771]
        g_data = df_g[df_g.iloc[:, 0] == label].iloc[:, 1:86771]
        b_data = df_b[df_b.iloc[:, 0] == label].iloc[:, 1:86771]

        # 计算平均值并四舍五入为整数
        r_avg = r_data.mean().round().astype(int)
        g_avg = g_data.mean().round().astype(int)
        b_avg = b_data.mean().round().astype(int)

        # 创建包含平均值的新数据框
        df_r_avg = pd.DataFrame([np.concatenate(([label], r_avg.values))])
        df_g_avg = pd.DataFrame([np.concatenate(([label], g_avg.values))])
        df_b_avg = pd.DataFrame([np.concatenate(([label], b_avg.values))])

        # 使用process_image函数处理平均图像
        process_image(0, df_r_avg, df_g_avg, df_b_avg, w, h, output_folder)

    print("所有类别的平均图像已处理完成。")


# 分割数据
def split_data(source_folder, train_folder, test_folder, test_size=0.2):
    """
    将源文件夹下的文件按指定比例拆分为训练集和测试集。
    source_folder = 'qr_img' # 原始数据集文件夹路径
    train_folder = 'qr_img_train' # 训练集的文件夹路径
    test_folder = 'qr_img_test' # 测试集的文件夹路径
    """
    classes = [d for d in os.listdir(source_folder) if os.path.isdir(os.path.join(source_folder, d))]
    for cls in classes:
        # 创建类别的训练和测试文件夹
        os.makedirs(os.path.join(train_folder, cls), exist_ok=True)
        os.makedirs(os.path.join(test_folder, cls), exist_ok=True)
        # 获取每个类别下的图像
        images = [f for f in os.listdir(os.path.join(source_folder, cls)) if
        os.path.isfile(os.path.join(source_folder, cls, f))]
        # 拆分数据集
        train_images, test_images = train_test_split(images, test_size=test_size)
        # 复制图像到新的训练和测试文件夹
        for image in train_images:
            shutil.copy(os.path.join(source_folder, cls, image), os.path.join(train_folder, cls, image))
        for image in test_images:
            shutil.copy(os.path.join(source_folder, cls, image), os.path.join(test_folder, cls, image))


# 合成图像
def process_image(i, df_r, df_g, df_b, w, h, output_folder):
    # 获取图像的标签
    label = df_r.iloc[i, 0]
    # 获取图像的索引
    index = df_r.index[i]
    # 获取图像的红色通道
    img_R = df_r.iloc[i, 1:].values.reshape(w, h)
    # 获取图像的绿色通道
    img_G = df_g.iloc[i, 1:].values.reshape(w, h)
    # 获取图像的蓝色通道
    img_B = df_b.iloc[i, 1:].values.reshape(w, h)

    # 将三个通道合并为一个彩色图像
    img_color = np.stack((img_R, img_G, img_B), axis=-1).astype(np.uint8)

    # 创建输出文件夹
    label_folder = os.path.join(output_folder, str(label))
    os.makedirs(label_folder, exist_ok=True)

    # 从数组中创建图像，并保存到指定文件夹
    img = Image.fromarray(img_color)
    # 保存图像，禁用抗锯齿
    img.save(os.path.join(label_folder, f'{label}_{index}.png'), optimize=True, quality=95, subsampling=0)


# 合并像素-新方法
def merge_pixels_new(df_r, df_g, df_b, w, h, output_folder='Imgs'):
    """
    转换数值为像素，合并每个通道成彩色图像
    :param df_r: 输入 R 通道数据，数据类型 pandas
    :param df_g: 输入 G 通道数据，数据类型 pandas
    :param df_b: 输入 B 通道数据，数据类型 pandas
    :param w: 要合并生成的彩色图像尺寸-宽度
    :param h: 要合并生成的彩色图像尺寸-高度
    :param output_folder: 生成的合并后图像要保存的路径
    :return: 无返回值
    """
    os.makedirs(output_folder, exist_ok=True)
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = []
        for i in range(len(df_r)):
            futures.append(executor.submit(process_image, i, df_r, df_g, df_b, w, h, output_folder))
        for future in tqdm(concurrent.futures.as_completed(futures), total=len(futures)):
            future.result()
    print("合并完成")


# 合并像素【旧方法，废弃】，效率比较慢
def merge_pixels_old(df_r, df_g, df_b, w, h, output_folder = 'Imgs'):
    """
    转换数值为像素，合并每个通道成彩色图像
    :param df_r: 输入 R 通道数据，数据类型 pandas
    :param df_g: 输入 G 通道数据，数据类型 pandas
    :param df_b: 输入 B 通道数据，数据类型 pandas
    :param w: 要合并生成的彩色图像尺寸-宽度
    :param h: 要合并生成的彩色图像尺寸-高度
    :param output_folder: 生成的合并后图像要保存的路径
    :return: 无返回值
    """
    os.makedirs(output_folder, exist_ok=True)
    # 遍历每一行数据
    for i in tqdm(range(len(df_r))):
        # 获取标签
        label = df_r.iloc[i, 0]
        # 获取行索引
        index = df_r.index[i]
        # 从 R, G, B 数据帧获取特征值并重塑成图像的宽高格式
        img_R = df_r.iloc[i, 1:].values.reshape(w, h)
        img_G = df_g.iloc[i, 1:].values.reshape(w, h)
        img_B = df_b.iloc[i, 1:].values.reshape(w, h)
        # 合并 R, G, B 通道来创建一个彩色图像
        img_color = np.stack((img_R, img_G, img_B), axis=-1).astype(np.uint8)
        # 创建类别文件夹，如果不存在的话
        label_folder = os.path.join(output_folder, str(label))
        os.makedirs(label_folder, exist_ok=True)
        # 使用 matplotlib 保存图像
        plt.imshow(img_color)
        plt.axis('off') # 不显示坐标轴
        # 保存图像
        plt.savefig(os.path.join(label_folder, f'{label}_{index}.png'), bbox_inches='tight', pad_inches=0)
        plt.close()
    print("合并完成")


# 数据增强
def data_aug(df):
    # 检查属性数据是否全部非0，返回一个布尔数组
    non_zero_rows = df.iloc[:, 1:].apply(lambda x: (x != 0).all(), axis=1)
    # 初始化列表来收集行
    rows_to_add = []
    # 遍历每一行
    for index, row in tqdm(df[non_zero_rows].iterrows()):
        # 对于每个属性
        for col in df.columns[1:]:
            # 创建一个新行，其中一个属性被设置为0
            new_row = row.copy()
            new_row[col] = 0
            # 将新行添加到列表中
            rows_to_add.append(new_row)
    # 从列表创建一个新的 DataFrame
    augmented_rows = pd.DataFrame(rows_to_add, columns=df.columns)
    # 为原始数据添加标记列（未增强）
    df['augmented'] = 0
    # 为增强数据添加标记列（已增强）
    augmented_rows['augmented'] = 1
    # 合并原始数据和增强数据
    final_df = pd.concat([df, augmented_rows], ignore_index=True)
    # 保存到parquet文件
    final_df.to_parquet('Data/augmented_data.parquet')
    print("保存成功")
    return final_df


# 计算excel数据完整程度
def cal_completion(df, name, s=1, d=13):
    """
    计算数据完整度
    :param df: 输入要计算完整度的数据，数据类型：pandas数据框
    :param s: 输入要计算完整度的数据的起始列索引
    :param d: 输入要计算完整度的数据的结束列索引
    :param name: 输入要计算完整度的数据对应的文件名
    :return: 返回计算好的完整度数据，数据类型：pandas数据框
    """
    # 计算完整度
    df['Completion'] = df.iloc[:, s:d].sum(axis=1) / 14
    df['Completion'] = df['Completion'].round().astype(int)
    # 确保非全0行的最低值为 1
    df['Completion'] = df.apply(lambda x: max(x['Completion'], 1) if x.iloc[s:d].sum() > 0 else x['Completion'], axis=1)
    # 导出到Excel文件
    convert_to_excel(df, name)
    print("完整度计算成功")
    return df


# 读取 excel 文件
def read_excel(file_path):
    return pd.read_excel(file_path)


# 切分数据
def split_dataframe(df, interval=14):
    """
    切分数据集成三个部分-R G B（以 14 个为间隔）
    :param df: 输入要切分的数据，数据类型：pandas数据框
    :param interval: 输入要切分的数据的间隔
    :return: 返回切分好的三个部分， 数据类型: pandas数据框
    """
    # 确保df至少有一列
    if df.shape[1] < 2:
        raise ValueError("DataFrame至少需要有两列")
    # 获取第一列
    first_col = df.iloc[:, [0]]
    # 第一个部分的列索引范围
    part1_cols = list(range(1, min(1 + interval, df.shape[1])))
    # 第二个部分的列索引范围
    part2_cols = list(range(15, min(1 + interval*2, df.shape[1])))
    # 第三个部分的列索引范围
    part3_cols = list(range(1 + interval*2, df.shape[1]))
    # 创建每个部分
    part1 = pd.concat([first_col, df.iloc[:, part1_cols]], axis=1)
    part2 = pd.concat([first_col, df.iloc[:, part2_cols]], axis=1)
    part3 = pd.concat([first_col, df.iloc[:, part3_cols]], axis=1)
    return part1, part2, part3


def compute_quantiles(data, n_quantiles=255):
    """
    计算给定数据的等级。
    """
    # 移除NaN值和0值
    data_clean = data[(data != 0) & ~data.isna()]
    quantiles = np.percentile(data_clean, np.linspace(0, 100, n_quantiles + 1)[1:-1])
    return quantiles


def map_to_quantiles(data, quantiles):
    """
    将数据映射到256个类别中，根据提供的255个阈值。
    """
    # 确保quantiles是有序的
    quantiles = np.sort(quantiles)
    # 初始化所有值为0类别
    grades = np.zeros(data.shape, dtype=int)
    # 处理非0和非NaN值，使用digitize函数分配类别
    non_zero_non_na_indices = (data != 0) & ~pd.isna(data)
    grades[non_zero_non_na_indices] = np.digitize(data[non_zero_non_na_indices], quantiles) + 1  # 加1确保映射到1-255类别
    return grades


def map_to_quantiles_cl(quantiles):
    """
    使用命令行来检验输入数据的类别映射
    """
    # 循环接收输入
    while True:
        user_input = input("请输入一个数值（输入'q'进入下一个特征列验证） ")
        if user_input.lower() == 'q':
            break
        try:
            # 将输入转换为浮点数，并映射到类别中
            data_value = float(user_input)
            category = map_to_quantiles(np.array([data_value]), quantiles)[0]
            print(f"值 {data_value} 映射到类别 {category}")
        except ValueError:
            print("请输入一个有效的数值或'q'退出")


def draw_map_to_quantiles(element_data, grades):
    """
    绘制 256 分位映射图
    :param element_data: 原始数据，数据类型 pandas
    :param grades: 对应的分为等级
    :return: 无返回值
    """
    plt.figure(figsize=(10, 6))
    plt.scatter(element_data, grades, alpha=0.6, edgecolors='w', linewidth=0.5)
    plt.title('Data Value vs. Mapped Category')
    plt.xlabel('Data Value')
    plt.ylabel('Mapped Category')
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    plt.show()


def grads_verify_all(df, is_verify):
    """
    验证等级计算是否正确，并保存分类结果
    :param df: 要验证的数据
    :param is_verify: 是否启用验证？ True 启用验证映射是否正确
    :return: 无返回值
    """
    # 创建一个空的 DataFrame 来存储所有分位数数据
    all_quantiles = pd.DataFrame()

    col_index = 0
    for col in df.columns[1:]:
        # 计算每一列的分位数
        quantiles = compute_quantiles(df[col])
        col_index += 1

        # 将分位数添加到 all_quantiles DataFrame
        all_quantiles[df.columns[col_index]] = pd.Series(quantiles)

        if is_verify:
            # 输出分位数
            print(f"当前特征列为：{df.columns[col_index]}，其分位数间隔详细数据如下所示：")
            print(quantiles)
            map_to_quantiles_cl(quantiles)
            draw_map_to_quantiles(df[col], map_to_quantiles(df[col], quantiles))
        # 将每个值映射到相应的类别
        df[col] = map_to_quantiles(df[col], quantiles)

    # 将所有分位数数据写入一个 Excel 文件
    all_quantiles.to_excel('Quan_Data/all_quantiles.xlsx', index=False)

    # 将处理后的数据框写入Excel文件
    df.to_excel('processed_data.xlsx', index=False)
    print("分位数归类完成")


def grads_verify(df,is_verify):
    """
    验证等级计算是否正确，并保存分类结果
    :param df: 要验证的数据
    :param is_verify: 是否启用验证？ True 启用验证映射是否正确
    :return: 无返回值
    """
    col_index = 0
    for col in df.columns[1:]:
        # 计算每一列的分位数
        quantiles = compute_quantiles(df[col])
        col_index += 1

        pd.Series(quantiles, name='Quantiles').to_excel(f'Quan_Data/{df.columns[col_index]}_quantiles.xlsx', index=False)

        if is_verify:
            # 输出分位数
            print(f"当前特征列为：{df.columns[col_index]}，其分位数间隔详细数据如下所示：")
            print(quantiles)
            map_to_quantiles_cl(quantiles)
            draw_map_to_quantiles(df[col], map_to_quantiles(df[col], quantiles))
        # 将每个值映射到相应的类别
        df[col] = map_to_quantiles(df[col], quantiles)
    # 将处理后的数据框写入Excel文件
    df.to_excel('processed_data.xlsx', index=False)
    print("分位数归类完成")


# 填充空值为 0 值
def fill_zero(file_path):
    """
    填充空值为 0 值
    :param file_path: 输入文件路径
    :return: 无返回值
    """
    df_file = pq.ParquetFile(file_path)  # 读取文件
    table = df_file.read()  # 读取数据
    df = table.to_pandas()  # 转换为 pandas 数据框
    df_filled = df.fillna(0)  # 填充空值为 0
    table_filled = pa.Table.from_pandas(df_filled)  # 写回数据框
    pq.write_table(table_filled, 'Data/filled_example.parquet')  # 写入新的文件


# 非线性标准化-分位数缩放
def nonlinear_scaled_256_0(df):
    """
    对数据进行非线性标准化，缩放到 0-255，采用的是分位数，默认排除第一列，即从第二列开始到最后的数据进行缩放
    :param df: 数据集
    :return: 返回缩放后的数据
    """
    features = df.iloc[:, 1:]
    # 使用分位数变换，减少离群值的影响
    scaler = QuantileTransformer(output_distribution='uniform')
    scaled_features = scaler.fit_transform(features)
    # 将数据线性缩放到0-255范围
    scaler = MinMaxScaler(feature_range=(0, 255))
    scaled_features = scaler.fit_transform(scaled_features)
    # 确保标准化后的数据是整数
    scaled_features = np.rint(scaled_features).astype(np.uint8)
    return scaled_features


# 读取 parquet 文件
def read_parquet(file_path):
    """
    读取 parquet 文件
    :param file_path: 文件路径
    :return: 返回读取数据，数据类型 dataframe
    """
    df = pd.read_parquet(file_path)
    return df


# 将 dataframe 数据转换为 parquet 文件
def convert_df_to_parquet(df, new_filename="null"):
    """
    将 dataframe 数据转换为 parquet 文件
    :param df: 输入数据
    :param new_filename: 新文件的名称
    :return:
    """
    filename = new_filename if new_filename != "null" else "new.parquet"
    df.to_parquet(f"Data/{filename}", engine='pyarrow')  # 写入新的文件
    print(f"文件生成路径：Data/{filename}")


def convert_to_parquet(excel_file, new_filename="null"):
    """
    传入 excel 文件转换为 parquet 文件
    :param excel_file: excel文件的路径
    :param new_filename: 新文件名称，默认可缺省
    :return: 无返回值
    """
    df = pd.read_excel(excel_file)
    filename = new_filename if new_filename != "null" else "new.parquet"
    df.to_parquet(f"Data/{filename}", engine='pyarrow')  # 写入新的文件
    print(f"文件生成路径：Data/{filename}")


def convert_to_excel(df, new_filename="null"):
    """
    将 dataframe 数据转换为 excel 文件
    :param df: 输入数据
    :param new_filename: 新文件的名称
    :return:
    """
    filename = new_filename if new_filename != "null" else "new_excel.parquet"
    df.to_excel(f"Data/{filename}", index=False)
    print(f"文件生成路径：Data/{filename}")


# 计算地球化学元素的频度-热图展示
def geo_frequency_hot_plot(df, lim, start_index=1):
    """
    计算特征属性的频度，并绘制热图展示，默认计算范围是从第二列开始（包含）到最后一列结束
    :param df: 输入的数据集，数据类型 Dataframe
    :param lim: 设置计算阈值限制
    :param start_index:  初始列
    :return: 无返回值
    """
    columns = df.columns[start_index:]
    selected_df = df[columns]
    # 计算每列非空和非0值的比例
    non_zero_non_null_percentage = selected_df.apply(lambda x: ((x.notnull() & (x != 0)).sum() / len(x)) * 100)

    # 分成五部分
    part_size = len(non_zero_non_null_percentage) // 5 + (1 if len(non_zero_non_null_percentage) % 5 > 0 else 0)
    parts = [non_zero_non_null_percentage.iloc[i * part_size:(i + 1) * part_size] for i in range(5)]

    # 设置画布和网格
    plt.figure(figsize=(15, 20))  # 减少总体高度
    gs = gridspec.GridSpec(5, 2, width_ratios=[15, 1], height_ratios=[1, 1, 1, 1, 1], wspace=0.05, hspace=0.5)  # 增加垂直间距
    temp_index = len(df.columns) - 1        # 去掉标签列

    for i, part in enumerate(parts):
        ax = plt.subplot(gs[i, 0])
        sns.heatmap(part.values.reshape(1, -1), annot=True, fmt=".2f", cmap='YlGn', cbar=False)
        cleaned_labels = [re.sub(r"\(.*?\)", "", label).strip() for label in part.index]  # 清除括号及其内容
        ax.set_xticks(np.arange(len(part)) + 0.5)
        ax.set_xticklabels(cleaned_labels, rotation='vertical', ha="center")

        # 将每列非空和非0值的数量低于25%总行数的坐标轴标签变成红色
        for j, label in enumerate(ax.get_xticklabels()):
            if part.iloc[j] < lim:
                label.set_color('red')
                temp_index = temp_index - 1
        ax.set_yticks([])

    print(f"过线的条目是{temp_index}")
    # 右侧的热度条
    ax_cbar = plt.subplot(gs[:, 1])
    cmap = sns.color_palette("YlGn", as_cmap=True)
    norm = plt.Normalize(vmin=non_zero_non_null_percentage.min(), vmax=non_zero_non_null_percentage.max())
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    plt.colorbar(sm, cax=ax_cbar)
    ax_cbar.yaxis.tick_right()
    plt.show()

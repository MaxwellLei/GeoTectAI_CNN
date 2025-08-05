import CommonHelper as ch


# 入口函数
def main():
    pd = ch.read_parquet('Data/new.parquet')
    print(pd.head())

    ch.grads_verify_all(pd,False)


if __name__ == '__main__':
    main()


# 一些历史代码
def used():
    # 将数据转换为 parquet 文件提高读取速度
    # ch.convert_to_parquet('Data/[4]DataSet_Standard(排除频度少于33%的数据,剔除全空值) .xlsx')

    # 读取转换后的文件
    # pd = ch.read_parquet('Data/new.parquet')
    # 展示数据内容
    # print(pd.head())

    # 绘制 25% 范围的数据热图
    # ch.geo_frequency_hot_plot(pd,25)

    # 填充 0 值
    # ch.fill_zero("Data/new.parquet")

    # 读取填充 0 值后的文件
    # pd = ch.read_parquet('Data/filled_example.parquet')
    # 展示数据内容
    # print(pd.head())

    # ch.grads_verify(pd,False)

    # 转换 excel 文件为 parquet
    # ch.convert_to_parquet('Data/processed_data.xlsx', '分位数切分.parquet')

    # 读取 processed_data.xlsx 文件
    # pd = ch.read_excel('Data/processed_data.xlsx')
    # df = ch.data_aug(pd)
    # print(df)

    # # 读取 parquet 文件
    # pd = ch.read_parquet('Data/augmented_data.parquet')
    # # 展示数据内容
    # print(pd.head())
    # # 切分数据
    # part1,part2,part3 = ch.split_dataframe(pd)
    # # 保存切分后的数据
    # ch.convert_to_excel(part1, 'part1.xlsx')        # 主量元素 R
    # ch.convert_to_excel(part2, 'part2.xlsx')        # 微量元素 G
    # ch.convert_to_excel(part3, 'part3.xlsx')        # 其他元素 B

    # 读取每个部分的数据
    # # pd1 = ch.read_excel('Data/part1.xlsx')
    # pd2 = ch.read_excel('Data/part2_new.xlsx')
    # pd3 = ch.read_excel('Data/part3_new.xlsx')
    #
    # # 计算每个部分的数据完整度
    # # ch.cal_completion(pd1,'part1_new.xlsx')
    # ch.cal_completion(pd2,'part2_new_.xlsx')
    # ch.cal_completion(pd3,'part3_new_.xlsx')

    # 读取最终完整数据集文件
    # pd1 = ch.read_parquet('Data/part1_new_f.parquet')
    # pd2 = ch.read_parquet('Data/part2_new_f.parquet')
    # pd3 = ch.read_parquet('Data/part3_new_f.parquet')
    # # 展示数据内容
    # print(pd1.head())
    # print(pd2.head())
    # print(pd3.head())

    # 合并数据集成像素图
    # ch.merge_pixels_new(pd1,pd2,pd3,5,3)

    # ch.split_data('Imgs','DataSet/TrainDataSet','DataSet/TestDataSet')

    pf1 = ch.read_parquet('Data/part1_new_f.parquet')
    pf2 = ch.read_parquet('Data/part2_new_f.parquet')
    pf3 = ch.read_parquet('Data/part3_new_f.parquet')

    ch.cal_img(pf1, pf2, pf3, 5, 3, 'SampleImgs')

    pd = ch.read_parquet("Data/filled_example.parquet")
    print(pd.head())
    ch.grads_verify(pd, True)

    ch.process_dataset("DataSet_new/AnalsisData/TestDataSet", "DataSet_new/AnalsisData/完整标记文件.xlsx")

    pass








[🇺🇸 English Version]() 

# 前言

项目使用的是 `PyQT5` 开发技术，依赖于 `Python` 语言，本软件不建议学习代码风格，因为这是我第一次使用 `Python` 编写桌面软件，对于习惯使用 `WPF` 的 `Xaml` 编程来说，`PyQT5` 尽管上手很快，但是编写依旧是个噩梦，起码对于这次来说是的，软件没有使用任何架构，以至于维护它将会是一个吃力的事情🤮，我会尽量保持它没有任何恶性的 Bug。

我想对于我来说，写完这次 `PyQT5` 来说，是一个难忘的经历，虽然我很喜欢编程，但是对于一个软件能让我比较烦躁的去写代码的来说，这是头一次，可能这只是因为我不太熟悉 `PyQT5` 的库的缘故吧，又或者是我过多的习惯于微软提供的便利工具吧🤔

> 茶歇的时候拿了香蕉，手我觉得自己像一只猴子。不仅听不懂别人在说什么，还在旁边吃香蕉🍌。

# GeoTectAI_CNN 说明

本项目使用 `PyQT5` 你应该看见前面的说明了，用 `Python 3.10.14` 写桌面软件我总感觉是灾难性的，起码在打包的时候是这样的，本项目想希望使用**玄武岩**更**高维度**的**地球化学数据**来区分构造环境类别，通过使用 42 个特征元素训练卷积神经网络来判别。

感谢相关库及其开发者的支持，这个项目主要依赖于如下列表的库（除了 Python 标准库）：

* QFluentWidgets
* Matplotlib
* PyQt5
* numpy
* PyTorch

如果你想进一步编译这个项目的话，请你先安装如上的库，软件只会打包一个 Windows 版本的，可能会有一点大，我本人对于 `Python` 打包项目并不熟练。

如果你在使用过程中有任何问题，都可以在项目下面的 **Issues** 留言。

# 数据集

数据来源于大型地球化学数据库[GEOROC](http://georoc.mpch-mainz.gwdg.de/georoc/)（🌹**感谢数据库和众多研究人员提供数据支持**🌹），本项目的训练数据集将会存储在项目的 `DataSet` 文件中。具体数据和预处理过程，我会在后面进行公布和说明。

# 卷积神经网络模型

模型的结构会在后续公布，关于训练，测试，解译卷积神经网络模型的代码将会存放在 `ML_Code` 文件夹中。

需要注意的是：在调用相关代码的时候，请确保你安装了相关的包。

# 软件的流程

软件分为：**主页，预测模块，设置模块**。

* 在主页你可以看到相关说明
* 在预测模块中，分为三个流程
  1. **导入数据**，进行初步设置，例如：标题行，自动匹配模式
  2. **验证并匹配数据**，对导入的数据进行检查和匹配，建立映射，为了下一步预测做准备
  3. **进行模型预测**，我使用了多线程操作，不过我还是建议你在进行预测的时候不要做其他非法操作。在预测结束后，结果会显示在相关卡片上，你可以通过点击数据内容的某一项，来查看具体某一项的预测概率值。我们会将预测结果添加到数据内容的最后一列，并且命名最后一列为 `predict_res` ，你可以通过导出预测结果来查看。
* 在设置中，你可以切换主题，风格，语言等选项

因为这次软件使用的是纯 `Python` 开发，所以对于深度学习的代码部分，我也并不需要通过第三方来调用，所以项目代码上会相对简单。

# 截图

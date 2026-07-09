# msxx\_fontlib

PSP《*Metal Slug XX*》字体纹理图`FONT_LIB.BIN`文件解析与仿制工具套件。

## 套件构成

1. `msxx_fontlib.py`：用于解析`FONT_LIB.BIN`字图库文件、根据工程文件重建字图库文件。
2. `atlas_gen.py`：能生成`1`程序所用的工程文件。
3. `charset_gen.py`：读取[`msxx_txt`](https://github.com/wyz-2015/msxx_txt/)生成的json文件并得出其所用字符集合的工具。适合配合`2`程序使用。

## 用法

此为命令行工具，请积极使用`--help`选项查询。

### 用例

#### 读取

读取字体文件，并打印元数据：

```
$ ./msxx_fontlib.py read ./FONT_LIB.BIN
```

读取字体文件，并提取信息保存到当前目录下的子目录`./D/`中：

```
$ ./msxx_fontlib.py read ./FONT_LIB.BIN -d ./D/
```

#### 制作

制作过程有点类似`cmake`与`make`。

1. 为了不令工作目录显得凌乱，建议在一个新建的工作目录里着手制作。这里举例为程序所在目录的子目录`./example/`。
2. 用工具`atlas_gen.py`，读取`proj.json`，生成`Makefile.json`及其相关数据。

    ```
    $ ./../atlas_gen.py ./proj.json
    ```

3. 然后制作`FONT_LIB.BIN`:

    ```
    $ ./../msxx_fontlib.py write
    ```

    或

    ```
    $ ./../msxx_fontlib.py write -f ./Makefile.json
    ```

##### `proj.json`的格式定义

请着重参考`./sample/proj.json`。

1. `charSize`为用`Pillow`生成字时的字号(`size`参数)。
2. `pagePixSize`为一页纹理字图的宽、高，单位像素。
3. `fonts`中的每个条目：
    1. `fontFile`为指定TrueType字体文件
    2. `ttcIndex`，若字体文件是ttc集合字体文件，则用这个指定使用其中哪个子集。否则默认`0`即可。
    3. `border`：每个字符的下边距，单位像素。
    4. `superSample`超采样倍数。使用超采样生成的字体，最终看起来更“柔”一些。
    5. `charStr`与`charFile`，引入的字符。这两种键不一定都要出现。`charStr`直接以json字符串的形式记载字符，尤其适合存在`不可打印字符`的情况；`charFile`则从键值指定的文本文件中导入出现于其中的所有字符。最后将导入上述两种途径导入字符的并集。

## 依赖

* 库(于`Ubuntu 26.04`系统软件源中的名字)：`python3-numpy python3-pil`

## 参考文献

一批从*MSXX欧版*中逆向工程得到的代码`references.tar.xz`已随附。

[`KIMI AI`](https://kimi.moonshot.cn/)在解析这批代码上帮了大忙。

## LICENCE

`LGPL >= 3`

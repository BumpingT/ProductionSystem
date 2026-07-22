python : Traceback (most recent call last):
所在位置 行:1 字符: 72
+ ... ng=[Console]::OutputEncoding=[System.Text.Encoding]::UTF8;python -c "
+                                                               ~~~~~~~~~~~
    + CategoryInfo          : NotSpecified: (Traceback (most recent call last)::String) [], RemoteException
    + FullyQualifiedErrorId : NativeCommandError
 
  File "<string>", line 7, in <module>
    print(f'ECHARTS_SRC = \'\'\'{js_escaped}\'\'\'')
    ~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
UnicodeEncodeError: 'gbk' codec can't encode character '\u25b6' in position 584520: illegal multibyte sequence

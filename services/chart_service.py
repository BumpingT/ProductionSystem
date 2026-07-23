"""图表报表生成服务"""
import os, json, tempfile, shutil, webbrowser
from config import YEN, ECHARTS_PATH


def _chart_html(stats, title=''):
    """生成 ECharts 图表 HTML（修复：y轴标签显示不全、日产量趋势标签拥挤）"""
    t = stats['totals']; w = stats['by_worker']; d = stats['by_date']; p = stats['by_process']
    # 清洗数据：None 转 0 或空字符串
    for item in w:
        for k in ('q', 'e'):
            if item.get(k) is None: item[k] = 0
    for item in d:
        for k in ('q', 'e'):
            if item.get(k) is None: item[k] = 0
    for item in p:
        for k in ('q', 'e'):
            if item.get(k) is None: item[k] = 0
    # 清洗字符串字段
    for item in w:
        for k in ('worker', 'group_name'):
            if item.get(k) is None: item[k] = ''
    for item in d:
        for k in ('record_date',):
            if item.get(k) is None: item[k] = ''
    for item in p:
        for k in ('material', 'process_name'):
            if item.get(k) is None: item[k] = ''

    # ── 工人工价数据 ──
    w_data = [x['q'] for x in w]
    w_names = [x['worker'] for x in w]
    wj = json.dumps(w_data)

    # ── 日产量数据（动态计算标签间隔和旋转角度） ──
    n_dates = len(d)
    d_dates = [x['record_date'] for x in d]
    d_qty = [x['q'] for x in d]
    dj = json.dumps(d_qty)

    if n_dates > 30:
        d_rotate = 60
        d_interval = max(1, n_dates // 20)  # 最多显示约20个标签
    elif n_dates > 15:
        d_rotate = 45
        d_interval = max(1, n_dates // 12)  # 最多显示约12个标签
    elif n_dates > 8:
        d_rotate = 30
        d_interval = 0  # 全部显示
    else:
        d_rotate = 0
        d_interval = 0

    # ── 工序产量数据 ──
    p_data = [x['q'] for x in p]
    p_names = [(x['material'] or '') + '-' + (x['process_name'] or '') for x in p]
    pj = json.dumps(p_data)

    # ── 动态计算最大标签宽度 ──
    max_worker_w = max((len(n) * 12 for n in w_names), default=60)
    max_proc_w = max((len(n) * 11 for n in p_names), default=80)
    grid_left_w = max(max_worker_w + 30, 100)   # 工人排行y轴预留宽度
    grid_left_p = max(max_proc_w + 30, 120)      # 工序产量y轴预留宽度

    # ── 大量数据时启用滚动缩放 ──
    n_workers = len(w)
    n_procs = len(p)
    # 工人排行：超过10人时加滚动条
    if n_workers > 10:
        w_datazoom = '''dataZoom:[{type:"slider",yAxisIndex:0,height:12,bottom:0,show:true,start:0,end: Math.min(100,100*10/{n_workers}),borderColor:"#ccc",fillerColor:"rgba(26,115,232,0.15)",handleStyle:{{color:"#1a73e8"}}}},{{type:"inside",yAxisIndex:0,start:0,end:100}}],'''.format(n_workers=n_workers)
        w_height = 260 + n_workers * 3  # 人越多图表越高
    else:
        w_datazoom = ''
        w_height = 260
    # 工序产量：超过10条时加滚动条
    if n_procs > 10:
        p_datazoom = '''dataZoom:[{{type:"slider",yAxisIndex:0,height:12,bottom:0,show:true,start:0,end:Math.min(100,100*10/{n_procs})}},{{type:"inside",yAxisIndex:0}}],'''.format(n_procs=n_procs)
        p_height = 260 + n_procs * 3
    else:
        p_datazoom = ''
        p_height = 260

    # ── 日产量趋势底部预留空间（根据旋转角度） ──
    if d_rotate >= 45:
        grid_bottom = 80
    elif d_rotate >= 30:
        grid_bottom = 60
    else:
        grid_bottom = 40

    return f'''<!DOCTYPE html><html><head><meta charset="utf-8"><script src="echarts.min.js"></script>
<style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Microsoft YaHei,sans-serif;background:#f0f2f5;padding:20px}}
.sr{{display:flex;gap:12px;margin-bottom:16px}}
.sc{{flex:1;background:#fff;border-radius:8px;padding:14px;text-align:center;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.l{{font-size:12px;color:#888}} .v{{font-size:20px;font-weight:700;color:#2c3e50;margin-top:4px}}
.o{{font-size:11px;color:#27ae60}} .cc{{background:#fff;border-radius:8px;padding:14px;margin-bottom:14px;box-shadow:0 1px 3px rgba(0,0,0,.06)}}
.cb{{width:100%;min-height:220px}} table{{width:100%;border-collapse:collapse;font-size:12px}}
th{{background:#f7f8fa;padding:6px 8px;text-align:left;border-bottom:2px solid #e8e8e8}}
td{{padding:5px 8px;border-bottom:1px solid #f0f0f0}} h3{{font-size:13px;color:#555;margin-bottom:8px}}
</style></head><body>
<h2 style="margin-bottom:12px">{title}</h2>
<div class="sr"><div class="sc"><div class="l">\u5de5\u4eba\u6570</div><div class="v">{t["w"]}</div></div>
<div class="sc"><div class="l">\u603b\u4ea7\u91cf</div><div class="v">{t["q"]}</div></div>
<div class="sc"><div class="l">\u603b\u5de5\u4ef7</div><div class="v">{YEN}{round(t["e"],2)}</div></div>
<div class="sc"><div class="l">\u8bb0\u5f55\u6570</div><div class="v">{t["r"]}</div></div></div>
<div class="cc"><h3>\u5de5\u4eba\u5de5\u4ef7\u6392\u884c</h3><div id="w" class="cb" style="min-height:{w_height}px"></div></div>
<div class="cc"><h3>\u65e5\u4ea7\u91cf\u8d8b\u52bf</h3><div id="d" class="cb"></div></div>
<div class="cc"><h3>\u5de5\u5e8f\u4ea7\u91cf\u5206\u5e03</h3><div id="p" class="cb" style="min-height:{p_height}px"></div></div>
<script>
var wc=echarts.init(document.getElementById("w"));wc.setOption({{title:{{show:false}},tooltip:{{trigger:"axis",axisPointer:{{type:"shadow"}}}},grid:{{left:{grid_left_w},right:60,top:20,bottom:20}},xAxis:{{type:"value",name:"\u5de5\u4ef7({YEN})",nameLocation:"middle",nameGap:25,nameTextStyle:{{fontSize:11}}}},yAxis:{{type:"category",data:{json.dumps(w_names)},axisLabel:{{fontSize:11,width:{grid_left_w - 20},overflow:'truncate'}}}},{w_datazoom}series:[{{type:"bar",data:{wj},itemStyle:{{color:"#1a73e8",borderRadius:[0,4,4,0]}}}}]}});
var dc=echarts.init(document.getElementById("d"));dc.setOption({{title:{{show:false}},tooltip:{{trigger:"axis"}},grid:{{left:50,right:50,top:20,bottom:{grid_bottom}}},xAxis:{{type:"category",data:{json.dumps(d_dates)},axisLabel:{{rotate:{d_rotate},fontSize:10,interval:{d_interval}}},axisLine:{{onZero:false}}}},yAxis:{{type:"value",name:"\u4ea7\u91cf",nameLocation:"middle",nameGap:35,nameTextStyle:{{fontSize:11}}}},series:[{{type:"line",data:{dj},smooth:true,lineStyle:{{color:"#27ae60"}},areaStyle:{{color:"#27ae60",opacity:.15}}}}]}});
var pc=echarts.init(document.getElementById("p"));pc.setOption({{title:{{show:false}},tooltip:{{trigger:"axis",axisPointer:{{type:"shadow"}}}},grid:{{left:{grid_left_p},right:60,top:20,bottom:20}},xAxis:{{type:"value",name:"\u4ea7\u91cf",nameLocation:"middle",nameGap:25,nameTextStyle:{{fontSize:11}}}},yAxis:{{type:"category",data:{json.dumps(p_names)},axisLabel:{{fontSize:10,width:{grid_left_p - 20},overflow:'truncate'}}}},{p_datazoom}series:[{{type:"bar",data:{pj},itemStyle:{{color:"#e67e22",borderRadius:[0,4,4,0]}}}}]}});
</script></body></html>'''


def gen_report(stats, title='\u751f\u4ea7\u8bb0\u5f55'):
    """生成报表并在浏览器打开"""
    html = _chart_html(stats, title)
    path = os.path.join(tempfile.gettempdir(), 'report.html')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(html)
    if os.path.exists(ECHARTS_PATH):
        shutil.copy(ECHARTS_PATH, os.path.join(tempfile.gettempdir(), 'echarts.min.js'))
    webbrowser.open('file://' + path)

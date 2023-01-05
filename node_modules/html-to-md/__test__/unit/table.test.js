import Table from '../../src/tags/table'

describe("test <table></table> tag",()=>{

  it('table default align style',()=>{
    let table=new Table(`<table>
<thead>
<tr>
<th><s>col-1</s></th>
<th>col-2</th>
<th>col-3</th>
</tr>
</thead>
<tbody>
<tr>
<td>data-1-left</td>
<td>data-1-center</td>
<td><code>data-1-right</code></td>
</tr>
<tr>
<td>data-2-left</td>
<td><b>data-2-center</b></td>
<td>data-2-right</td>
</tr>
<tr>
<td><i>data-3-left</i></td>
<td>data-3-center</td>
<td>data-3-right</td>
</tr>
</tbody>
</table>`)
    expect(table.exec()).toBe("\n" +
      "|~~col-1~~|col-2|col-3|\n" +
      "|---|---|---|\n" +
      "|data-1-left|data-1-center|`data-1-right`|\n" +
      "|data-2-left|**data-2-center**|data-2-right|\n" +
      "|*data-3-left*|data-3-center|data-3-right|\n")
  })

  it('table has align style',()=>{
    let table=new Table("<table class=\"table table-striped\">\n" +
      "<thead>\n" +
      "<tr>\n" +
      "<th style=\"text-align:left\"><s>col-1</s></th>\n" +
      "<th style=\"text-align:center\">col-2</th>\n" +
      "<th style=\"text-align:right\">col-3</th>\n" +
      "</tr>\n" +
      "</thead>\n" +
      "<tbody>\n" +
      "<tr>\n" +
      "<td style=\"text-align:left\">data-1-left</td>\n" +
      "<td style=\"text-align:center\">data-1-center</td>\n" +
      "<td style=\"text-align:right\"><code>data-1-right</code></td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td style=\"text-align:left\">data-2-left</td>\n" +
      "<td style=\"text-align:center\"><b>data-2-center</b></td>\n" +
      "<td style=\"text-align:right\">data-2-right</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td style=\"text-align:left\"><i>data-3-left</i></td>\n" +
      "<td style=\"text-align:center\">data-3-center</td>\n" +
      "<td style=\"text-align:right\">data-3-right</td>\n" +
      "</tr>\n" +
      "</tbody>\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "|~~col-1~~|col-2|col-3|\n" +
      "|:---|:---:|---:|\n" +
      "|data-1-left|data-1-center|`data-1-right`|\n" +
      "|data-2-left|**data-2-center**|data-2-right|\n" +
      "|*data-3-left*|data-3-center|data-3-right|\n")
  })

  it('table default align style, compact mode',()=>{
    let table=new Table(`<table><thead><tr><th><s>col-1</s></th><th>col-2</th><th>col-3</th></tr></thead><tbody><tr><td>data-1-left</td><td>data-1-center</td><td><code>data-1-right</code></td></tr><tr><td>data-2-left</td><td><b>data-2-center</b></td><td>data-2-right</td></tr><tr><td><i>data-3-left</i></td><td>data-3-center</td><td>data-3-right</td></tr></tbody></table>`)
    expect(table.exec()).toBe("\n" +
      "|~~col-1~~|col-2|col-3|\n" +
      "|---|---|---|\n" +
      "|data-1-left|data-1-center|`data-1-right`|\n" +
      "|data-2-left|**data-2-center**|data-2-right|\n" +
      "|*data-3-left*|data-3-center|data-3-right|\n")
  })

  it('table has text-align style, compact mode',()=>{
    let table=new Table(`<table class="table table-striped"><thead><tr><th style=\"text-align:left\"><s>col-1</s></th><th style=\"text-align:center\">col-2</th><th style=\"text-align:right\">col-3</th></tr></thead><tbody><tr><td style=\"text-align:left\">data-1-left</td><td style=\"text-align:center\">data-1-center</td><td style=\"text-align:right\"><code>data-1-right</code></td></tr><tr><td style=\"text-align:left\">data-2-left</td><td style=\"text-align:center\"><b>data-2-center</b></td><td style=\"text-align:right\">data-2-right</td></tr><tr><td style=\"text-align:left\"><i>data-3-left</i></td><td style=\"text-align:center\">data-3-center</td><td style=\"text-align:right\">data-3-right</td></tr></tbody></table>`)
    expect(table.exec()).toBe("\n" +
      "|~~col-1~~|col-2|col-3|\n" +
      "|:---|:---:|---:|\n" +
      "|data-1-left|data-1-center|`data-1-right`|\n" +
      "|data-2-left|**data-2-center**|data-2-right|\n" +
      "|*data-3-left*|data-3-center|data-3-right|\n")
  })

  it('table also support align style',()=>{
    let table=new Table(
`<table class="table table-striped">
  <thead>
    <tr>
      <th><s>col-1</s></th>
      <th>col-2</th>
      <th>col-3</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td align="left">data-1-left</td>
      <td align="center">data-1-center</td>
      <td align="right"><code>data-1-right</code></td>
    </tr>
    <tr>
      <td>data-2-left</td>
      <td><b>data-2-center</b></td>
      <td>data-2-right</td>
    </tr>
    <tr>
      <td><i>data-3-left</i></td>
      <td>data-3-center</td>
      <td>data-3-right</td>
    </tr>
  </tbody>
</table>
`)
    expect(table.exec()).toBe("\n" +
        "|~~col-1~~|col-2|col-3|\n" +
        "|:---|:---:|---:|\n" +
        "|data-1-left|data-1-center|`data-1-right`|\n" +
        "|data-2-left|**data-2-center**|data-2-right|\n" +
        "|*data-3-left*|data-3-center|data-3-right|\n")
  })


  it('table default align style, multi \n ',()=>{
    let table=new Table("<table>\n\n\n\n\n\n\n" +
      "<thead>\n\n\n\n\n\n\n" +
      "<tr>\n\n\n\n\n\n\n" +
      "<th><s>col-1</s></th>\n\n\n\n\n\n\n" +
      "<th>col-2</th>\n\n\n\n\n\n\n" +
      "<th>col-3</th>\n\n\n\n\n\n\n" +
      "</tr>\n\n\n\n\n\n\n" +
      "</thead>\n\n\n\n\n\n\n" +
      "<tbody>\n\n\n\n\n\n\n" +
      "<tr>\n\n\n\n\n\n\n" +
      "<td>data-1-left</td>\n\n\n\n\n\n\n" +
      "<td>data-1-center</td>\n\n\n\n\n\n\n" +
      "<td><code>data-1-right</code></td>\n\n\n\n\n\n\n" +
      "</tr>\n\n\n\n\n\n\n" +
      "<tr>\n\n\n\n\n\n\n" +
      "<td>data-2-left</td>\n\n\n\n\n\n\n" +
      "<td><b>data-2-center</b></td>\n\n\n\n\n\n\n" +
      "<td>data-2-right</td>\n\n\n\n\n\n\n" +
      "</tr>\n\n\n\n\n\n\n" +
      "<tr>\n\n\n\n\n\n\n" +
      "<td><i>data-3-left</i></td>\n\n\n\n\n\n\n" +
      "<td>data-3-center</td>\n\n\n\n\n\n\n" +
      "<td>data-3-right</td>\n\n\n\n\n\n\n" +
      "</tr>\n\n\n\n\n\n\n" +
      "</tbody>\n\n\n\n\n\n\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "|~~col-1~~|col-2|col-3|\n" +
      "|---|---|---|\n" +
      "|data-1-left|data-1-center|`data-1-right`|\n" +
      "|data-2-left|**data-2-center**|data-2-right|\n" +
      "|*data-3-left*|data-3-center|data-3-right|\n")
  })

  it('table has ignore tags, like <td><div>abc</div></td>',()=>{
    let table=new Table("<table>\n" +
      "<thead>\n" +
      "<tr>\n" +
      "<th><div>col-1</div></th>\n" +
      "<th>col-2</th>\n" +
      "</tr>\n" +
      "</thead>\n" +
      "<tbody>\n" +
      "<tr>\n" +
      "<td>data-1-left</td>\n" +
      "<td>data-1-center</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td>data-2-left</td>\n" +
      "<td><div>data-2-center</div></td>\n" +
      "</tr>\n"+
      "<tr>\n" +
      "<td><div>data-3-left</div></td>\n" +
      "<td>data-3-center</td>\n" +
      "</tr>\n" +
      "</tbody>\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "|col-1|col-2|\n" +
      "|---|---|\n" +
      "|data-1-left|data-1-center|\n" +
      "|data-2-left|data-2-center|\n" +
      "|data-3-left|data-3-center|\n")
  })

  it('table has ignore tags-2, like <td><div>abc</div></td>',()=>{
    let table=new Table("<table>\n" +
      "<thead>\n" +
      "<tr>\n" +
      "<th><div>col-1</div></th>\n" +
      "<th>col-2</th>\n" +
      "</tr>\n" +
      "</thead>\n" +
      "<tbody>\n" +
      "<tr>\n" +
      "<td>data-1-left</td>\n" +
      "<td>data-1-center</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td>data-2-left</td>\n" +
      "<td><div><div>data-2-center</div></div></td>\n" +
      "</tr>\n"+
      "<tr>\n" +
      "<td><div>data-3-left</div></td>\n" +
      "<td>data-3-center</td>\n" +
      "</tr>\n" +
      "</tbody>\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "|col-1|col-2|\n" +
      "|---|---|\n" +
      "|data-1-left|data-1-center|\n" +
      "|data-2-left|data-2-center|\n" +
      "|data-3-left|data-3-center|\n")
  })

  it('without thead',()=>{
    let table=new Table("<table>\n" +
      "\n" +
      "<tbody>\n" +
      "<tr>\n" +
      "<td>data-1-left</td>\n" +
      "<td>data-1-center</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td>data-2-left</td>\n" +
      "<td>data-2-center</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td>data-3-left</td>\n" +
      "<td>data-3-center</td>\n" +
      "</tr>\n" +
      "</tbody>\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "|||\n" +
      "|---|---|\n" +
      "|data-1-left|data-1-center|\n" +
      "|data-2-left|data-2-center|\n" +
      "|data-3-left|data-3-center|\n")
  })

  it('without tbody',()=>{
    let table=new Table("<table>\n" +
      "\n" +
      "<thead>\n" +
      "<tr>\n" +
      "<th>data-1-left</th>\n" +
      "<th>data-1-center</th>\n" +
      "</tr>\n" +
      "</thead>\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "|data-1-left|data-1-center|\n" +
      "|---|---|\n")
  })

  it('UL inside table(with css style)',()=>{
    let table=new Table("<table>\n" +
      "<thead>\n" +
      "<tr>\n" +
      "<th>Tables</th>\n" +
      "<th style=\"text-align:center\">Are</th>\n" +
      "<th style=\"text-align:right\">Cool</th>\n" +
      "</tr>\n" +
      "</thead>\n" +
      "<tbody>\n" +
      "<tr>\n" +
      "<td>col 3 is</td>\n" +
      "<td style=\"text-align:center\">right-aligned</td>\n" +
      "<td style=\"text-align:right\">$1600</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td><ul style='height:102px'>\n" +
      "          <li style='height:50px'>item1</li>\n" +
      "          <li>item2</li>\n" +
      "        </ul></td>\n" +
      "<td style=\"text-align:center\">See the list</td>\n" +
      "<td style=\"text-align:right\">from the first column</td>\n" +
      "</tr>\n" +
      "</tbody>\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "|Tables|Are|Cool|\n" +
      "|---|:---:|---:|\n" +
      "|col 3 is|right-aligned|$1600|\n" +
      "|<ul style='height:102px'>          <li style='height:50px'>item1</li>          <li>item2</li>        </ul>|See the list|from the first column|\n")
  })

  it('UL inside table(with css style and wrap)',()=>{
    let table=new Table("<table>\n" +
      "  <tbody>\n" +
      "    <tr>\n" +
      "      <th>Tables</th>\n" +
      "      <th align=\"center\">Are</th>\n" +
      "      <th align=\"right\">Cool</th>\n" +
      "    </tr>\n" +
      "    <tr>\n" +
      "      <td>col 3 is</td>\n" +
      "      <td align=\"center\">right-aligned</td>\n" +
      "      <td align=\"right\">$1600</td>\n" +
      "    </tr>\n" +
      "    <tr>\n" +
      "      <td>col 2 is</td>\n" +
      "      <td align=\"center\">centered</td>\n" +
      "      <td align=\"right\">$12</td>\n" +
      "    </tr>\n" +
      "    <tr>\n" +
      "      <td>zebra stripes</td>\n" +
      "      <td align=\"center\">are neat</td>\n" +
      "      <td align=\"right\">$1</td>\n" +
      "    </tr>\n" +
      "    <tr>\n" +
      "      <td>\n" +
      "        <ul>\n" +
      "          <li>item1</li>\n" +
      "          <li>item2</li>\n" +
      "        </ul>\n" +
      "      </td>\n" +
      "      <td align=\"center\">See the list</td>\n" +
      "      <td align=\"right\">from the first column</td>\n" +
      "    </tr>\n" +
      "  </tbody>\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "||||\n" +
      "|---|:---:|---:|\n" +
      "|Tables|Are|Cool|\n" +
      "|col 3 is|right-aligned|$1600|\n" +
      "|col 2 is|centered|$12|\n" +
      "|zebra stripes|are neat|$1|\n" +
      "|<ul>          <li>item1</li>          <li>item2</li>        </ul>|See the list|from the first column|\n")
  })

  it('OL inside table',()=>{
    let table=new Table("<table>\n" +
      "<thead>\n" +
      "<tr>\n" +
      "<th>Tables</th>\n" +
      "<th style=\"text-align:center\">Are</th>\n" +
      "<th style=\"text-align:right\">Cool</th>\n" +
      "</tr>\n" +
      "</thead>\n" +
      "<tbody>\n" +
      "<tr>\n" +
      "<td>col 3 is</td>\n" +
      "<td style=\"text-align:center\">right-aligned</td>\n" +
      "<td style=\"text-align:right\">$1600</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td><ol><li>item1</li><li>item2</li></ol></td>\n" +
      "<td style=\"text-align:center\">See the list</td>\n" +
      "<td style=\"text-align:right\">from the first column</td>\n" +
      "</tr>\n" +
      "</tbody>\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "|Tables|Are|Cool|\n" +
      "|---|:---:|---:|\n" +
      "|col 3 is|right-aligned|$1600|\n" +
      "|<ol><li>item1</li><li>item2</li></ol>|See the list|from the first column|\n")
  })

  it('Table inside table',()=>{
    let table=new Table("<table>\n" +
      "<thead>\n" +
      "<tr>\n" +
      "<th>Tables</th>\n" +
      "<th style=\"text-align:center\">Are</th>\n" +
      "</tr>\n" +
      "</thead>\n" +
      "<tbody>\n" +
      "<tr>\n" +
      "<td>col 3 is</td>\n" +
      "<td style=\"text-align:center\">right-aligned</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td><table><tbody><tr><td>1</td><td>2</td></tr></tbody></table></td>\n" +
      "<td style=\"text-align:center\">See the list</td>\n" +
      "</tr>\n" +
      "</tbody>\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "|Tables|Are|\n" +
      "|---|:---:|\n" +
      "|col 3 is|right-aligned|\n" +
      "|<table><tbody><tr><td>1</td><td>2</td></tr></tbody></table>|See the list|\n")
  })

  it('Pre inside table, still can not wrap...',()=>{
    let table=new Table("<table>\n" +
      "<thead>\n" +
      "<tr>\n" +
      "<th>Tables</th>\n" +
      "<th style=\"text-align:center\">Are</th>\n" +
      "</tr>\n" +
      "</thead>\n" +
      "<tbody>\n" +
      "<tr>\n" +
      "<td>col 3 is</td>\n" +
      "<td style=\"text-align:center\">right-aligned</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td><pre><code>function plus(){\n" +
      "    var a=5\n" +
      "    var b=7;\n" +
      "    return a+b\n" +
      "    }\n" +
      "</code></pre></td>\n" +
      "<td style=\"text-align:right\">from the first column</td>\n" +
      "</tr>\n" +
      "</tbody>\n" +
      "</table>")
    expect(table.exec()).toBe("\n" +
      "|Tables|Are|\n" +
      "|---|:---:|\n" +
      "|col 3 is|right-aligned|\n" +
      "|<pre><code>function plus(){    var a=5    var b=7;    return a+b    }</code></pre>|from the first column|\n")
  })

  it('Empty table1',()=>{
    let table=new Table("<table></table>")
    expect(table.exec()).toBe('')
  })

  it('Empty table2',()=>{
    let table=new Table("<table><tr>123</tr></table>")
    expect(table.exec()).toBe('')
  })

  it('Empty table3',()=>{
    let table=new Table("<table><tbody></tbody></table>")
    expect(table.exec()).toBe('')
  })
  it('Empty table4',()=>{
    let table=new Table("<table><thead></thead></table>")
    expect(table.exec()).toBe('')
  })

  it('Empty td need to be kept',()=>{
    let table=new Table(
  `<table>
    <thead>
      <tr>
        <td></td>
        <td></td>
        <td></td>
        <td>Foo</td>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td></td>
        <td></td>
        <td></td>
        <td>Bar</td>
      </tr>
    </tbody>
  </table>`)
    expect(table.exec()).toBe(
`
||||Foo|
|---|---|---|---|
||||Bar|
`
      )
  })

  it('| in table should be escape',()=>{
    let table=new Table("<table><tbody><tr><td>|||123</td></tr></tbody></table>")
    expect(table.exec()).toBe(
`
||
|---|
|\\|\\|\\|123|
`)
  })
})

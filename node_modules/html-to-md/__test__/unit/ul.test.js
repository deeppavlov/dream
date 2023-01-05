import html2Md from '../../src/index'
const UL_SPACE = 2
const OL_SPACE = 3
describe("test <ul></ul> tag", () => {

    it('unorder list', () => {
        let ul = html2Md('<ul>\n' +
            '<li>one</li>\n' +
            '<li>two</li>\n' +
            '<li>three</li>\n' +
            '</ul>')
        expect(ul).toBe(
            '* ' + ' '.repeat(UL_SPACE - 2) + 'one\n' +
            '* ' + ' '.repeat(UL_SPACE - 2) + 'two\n' +
            '* ' + ' '.repeat(UL_SPACE - 2) + 'three')
    })

    it('nest ul', () => {
        let ul = html2Md('<ul>\n' +
            '<li>one</li>\n' +
            '<li>two\n' +
            '<ul>\n' +
            '<li>one</li>\n' +
            '<li>two</li>\n' +
            '<li>three</li>\n' +
            '</ul>\n' +
            '</li>\n' +
            '<li>three</li>\n' +
            '</ul>')
        expect(ul).toBe(
            '* ' + ' '.repeat(UL_SPACE - 2) + 'one\n' +
            '* ' + ' '.repeat(UL_SPACE - 2) + 'two\n' +
            ' '.repeat(UL_SPACE) + '* ' + ' '.repeat(UL_SPACE - 2) + 'one\n' +
            ' '.repeat(UL_SPACE) + '* ' + ' '.repeat(UL_SPACE - 2) + 'two\n' +
            ' '.repeat(UL_SPACE) + '* ' + ' '.repeat(UL_SPACE - 2) + 'three\n' +
            '* ' + ' '.repeat(UL_SPACE - 2) + 'three')
    })


    it('nest ol', () => {
        let ul = html2Md('<ul>\n' +
            '<li>one</li>\n' +
            '<li>two\n' +
            '<ol>\n' +
            '<li>unorder-1</li>\n' +
            '<li>unorder-2</li>\n' +
            '<li>unorder-3</li>\n' +
            '</ol>\n' +
            '</li>\n' +
            '<li>three</li>\n' +
            '</ul>')
        expect(ul).toBe(
            '* ' + ' '.repeat(UL_SPACE - 2) + 'one\n' +
            '* ' + ' '.repeat(UL_SPACE - 2) + 'two\n' +
            ' '.repeat(UL_SPACE) + '1.' + ' '.repeat(OL_SPACE - 2) + 'unorder-1\n' +
            ' '.repeat(UL_SPACE) + '2.' + ' '.repeat(OL_SPACE - 2) + 'unorder-2\n' +
            ' '.repeat(UL_SPACE) + '3.' + ' '.repeat(OL_SPACE - 2) + 'unorder-3\n' +
            '* ' + ' '.repeat(UL_SPACE - 2) + 'three')
    })

    it('complicate nest', () => {
        let ul = html2Md('<ul>\n' +
            '<li><strong>STRONG</strong></li>\n' +
            '<li><a href="https://github.com/-it/markdown-it-sub">ATag</a>\n' +
            '<ol>\n' +
            '<li>unorder-1</li>\n' +
            '<li>unorder-2\n' +
            '<ul>\n' +
            '<li>one</li>\n' +
            '<li>two\n' +
            '<blockquote>\n' +
            '<ol>\n' +
            '<li>bq-nest-1</li>\n' +
            '</ol>\n' +
            '<blockquote>\n' +
            '<ol>\n' +
            '<li>bq-nest-2</li>\n' +
            '</ol>\n' +
            '<blockquote>\n' +
            '<ol>\n' +
            '<li>bq-nest-3</li>\n' +
            '</ol>\n' +
            '</blockquote>\n' +
            '</blockquote>\n' +
            '</blockquote>\n' +
            '</li>\n' +
            '</ul>\n' +
            '</li>\n' +
            '<li>unorder-3\n' +
            '<ol>\n' +
            '<li>code<pre class="hljs language-javascript"><code><span class="hljs-function"><span class="hljs-keyword">function</span> <span class="hljs-title">a</span>(<span class="hljs-params"></span>)</span>{\n' +
            '    <span class="hljs-keyword">let</span> b=<span class="hljs-number">5</span>\n' +
            '    <span class="hljs-keyword">let</span> obj={\n' +
            '            <span class="hljs-attr">x</span>:<span class="hljs-number">100</span>\n' +
            '        }\n' +
            '    <span class="hljs-keyword">return</span> obj.x+b\n' +
            '}\n' +
            '</code></pre>\n' +
            '</li>\n' +
            '</ol>\n' +
            '</li>\n' +
            '</ol>\n' +
            '</li>\n' +
            '<li>three</li>\n' +
            '</ul>')
        expect(ul).toBe(
            '*' + ' '.repeat(UL_SPACE - 1) + '**STRONG**\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + '[ATag](https://github.com/-it/markdown-it-sub)\n' +
            '\n'+
            ' '.repeat(UL_SPACE) + '1.' + ' '.repeat(OL_SPACE - 2) + 'unorder-1\n' +
            ' '.repeat(UL_SPACE) + '2.' + ' '.repeat(OL_SPACE - 2) + 'unorder-2\n' +
            ' '.repeat(UL_SPACE + OL_SPACE) + '*' + ' '.repeat(UL_SPACE - 1) + 'one\n' +
            ' '.repeat(UL_SPACE + OL_SPACE) + '*' + ' '.repeat(UL_SPACE - 1) + 'two\n' +
            ' '.repeat(UL_SPACE * 2 + OL_SPACE) + '> 1.' + ' '.repeat(OL_SPACE - 2) + 'bq-nest-1\n' +
            ' '.repeat(UL_SPACE * 2 + OL_SPACE) + '>\n' +
            ' '.repeat(UL_SPACE * 2 + OL_SPACE) + '>> 1.' + ' '.repeat(OL_SPACE - 2) + 'bq-nest-2\n' +
            ' '.repeat(UL_SPACE * 2 + OL_SPACE) + '>>\n' +
            ' '.repeat(UL_SPACE * 2 + OL_SPACE) + '>>> 1.' + ' '.repeat(OL_SPACE - 2) + 'bq-nest-3\n' +
            ' '.repeat(UL_SPACE) + '3.' + ' '.repeat(OL_SPACE - 2) + 'unorder-3\n' +
            ' '.repeat(UL_SPACE + OL_SPACE) + '1.' + ' '.repeat(OL_SPACE - 2) + 'code\n' +
            ' '.repeat(UL_SPACE + 2 * OL_SPACE) + '```javascript\n' +
            ' '.repeat(UL_SPACE + 2 * OL_SPACE) + 'function a(){\n' +
            ' '.repeat(UL_SPACE + 2 * OL_SPACE) + '    let b=5\n' +
            ' '.repeat(UL_SPACE + 2 * OL_SPACE) + '    let obj={\n' +
            ' '.repeat(UL_SPACE + 2 * OL_SPACE) + '            x:100\n' +
            ' '.repeat(UL_SPACE + 2 * OL_SPACE) + '        }\n' +
            ' '.repeat(UL_SPACE + 2 * OL_SPACE) + '    return obj.x+b\n' +
            ' '.repeat(UL_SPACE + 2 * OL_SPACE) + '}\n' +
            ' '.repeat(UL_SPACE + 2 * OL_SPACE) + '```\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + 'three')
    })

    it("li nest p", () => {
        let ul = html2Md("<ul>\n" +
            "<li>\n" +
            "<p>Lorem ipsum dolor sit amet</p></li>\n" +
            "<li><p>Consectetur adipiscing elit</p>\n" +
            "</li>\n" +
            "<li><p>Integer molestie lorem at massa</p></li>\n" +
            "<li>\n" +
            "<p>You can use sequential numbers…</p>\n" +
            "</li>\n" +
            "<li>\n" +
            "<p>…or keep all the numbers as <code>1.</code></p>\n" +
            "</li>\n" +
            "</ul>")

        expect(ul).toBe(
            '*' + ' '.repeat(UL_SPACE - 1) + 'Lorem ipsum dolor sit amet\n' +
            '\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + 'Consectetur adipiscing elit\n' +
            '\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + 'Integer molestie lorem at massa\n' +
            '\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + 'You can use sequential numbers…\n' +
            '\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + '…or keep all the numbers as `1.`')
    })

    it("text in li", () => {
        let ul = html2Md("<ul>\n" +
            "<li>Lorem ipsum dolor sit amet\n" +
            "</li>\n" +
            "<li>\n" +
            "Consectetur adipiscing elit</li>\n" +
            "<li>Integer molestie lorem at massa</li>\n" +
            "<li>\n" +
            "You can use sequential numbers…\n" +
            "</li>\n" +
            "<li>\n" +
            "…or keep all the numbers as <code>1.</code>\n" +
            "</li>\n" +
            "</ul>")

        expect(ul).toBe(
            '*' + ' '.repeat(UL_SPACE - 1) + 'Lorem ipsum dolor sit amet\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + 'Consectetur adipiscing elit\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + 'Integer molestie lorem at massa\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + 'You can use sequential numbers…\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + '…or keep all the numbers as `1.`')
    })

    it("todo list", () => {
        let ul = html2Md('<ul>\n' +
            '<li><input disabled="" type="checkbox"> not finish-1</li>\n' +
            '<li><input disabled="" type="checkbox"> not finish-2</li>\n' +
            '<li><input disabled="" type="checkbox"> not finish-3</li>\n' +
            '<li><input disabled="" type="checkbox"> not finish-4</li>\n' +
            '</ul>')

        expect(ul).toBe(
            '*' + ' '.repeat(UL_SPACE - 1) + '[ ]  not finish-1\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + '[ ]  not finish-2\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + '[ ]  not finish-3\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + '[ ]  not finish-4')
    })

    it("done list", () => {
        let ul = html2Md('<ul>\n' +
            '<li><input checked="" disabled="" type="checkbox"> finish-1</li>\n' +
            '<li><input checked="" disabled="" type="checkbox"> finish-2</li>\n' +
            '<li><input checked="" disabled="" type="checkbox"> finish-3</li>\n' +
            '<li><input checked="" disabled="" type="checkbox"> finish-4</li>\n' +
            '</ul>')

        expect(ul).toBe(
            '*' + ' '.repeat(UL_SPACE - 1) + '[x]  finish-1\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + '[x]  finish-2\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + '[x]  finish-3\n' +
            '*' + ' '.repeat(UL_SPACE - 1) + '[x]  finish-4')
    })

    it("test <br>", () => {
        let ul = html2Md('<ul>\n' +
            '<li><strong>参数replace</strong><br>\n' +
            '用来设置是否可以取相同元素：<br>\n' +
            'True表示可以取相同数字；<br>\n' +
            'False表示不可以取相同数字。<br>\n' +
            '默认是True</li>\n' +
            '</ul>')

        expect(ul).toBe(
            `* **参数replace**  
  用来设置是否可以取相同元素：  
  True表示可以取相同数字；  
  False表示不可以取相同数字。  
  默认是True`)
    })

    it("test <br> 2", () => {
        let ul = html2Md('<ul>\n' +
            '<li><strong>参数replace</strong><br>\n' +
            '用来设置是否可以取相同元素：<br>\n' +
            'True表示可以取相同数字；<br>\n' +
            '<ul>\n' +
            '<li><strong>nest参数replace</strong><br>\n' +
            'nest用来设置是否可以取相同元素：<br>\n' +
            'nestTrue表示可以取相同数字；<br>\n' +
            'nestFalse表示不可以取相同数字。<br>\n' +
            'nest默认是True</li>\n' +
            '</ul>' +
            '默认是True</li>\n' +
            '</ul>')

        expect(ul).toBe("* **参数replace**  \n" +
            "  用来设置是否可以取相同元素：  \n" +
            "  True表示可以取相同数字；  \n" +
            "\n" +
            "  * **nest参数replace**  \n" +
            "    nest用来设置是否可以取相同元素：  \n" +
            "    nestTrue表示可以取相同数字；  \n" +
            "    nestFalse表示不可以取相同数字。  \n" +
            "    nest默认是True\n" +
            "  默认是True")
    })


    it("nest ul-2", () => {
        let ul = html2Md(`<ul>
<li>Create a list by starting a line with <code>+</code>, <code>-</code>, or <code>*</code></li>
<li>Sub-lists are made by indenting 2 spaces:
<ul>
<li>Marker character change forces new list start:
<ul>
<li>Ac tristique libero volutpat at</li>
</ul>
<ul>
<li>Facilisis in pretium nisl aliquet</li>
</ul>
<ul>
<li>Nulla volutpat aliquam velit</li>
</ul>
</li>
</ul>
</li>
<li>Very easy!</li>
</ul>`)
        expect(ul).toBe("* Create a list by starting a line with `+`, `-`, or `*`\n" +
            "* Sub-lists are made by indenting 2 spaces:\n" +
            "  * Marker character change forces new list start:\n" +
            "    * Ac tristique libero volutpat at\n" +
            "\n" +
            "    * Facilisis in pretium nisl aliquet\n" +
            "\n" +
            "    * Nulla volutpat aliquam velit\n" +
            "* Very easy!")
    })
})


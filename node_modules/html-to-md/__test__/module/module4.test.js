import html2Md from '../../src/index'

describe('test special', () => {

  it('test-1', () => {
    let str = "<body"
    expect(html2Md(str)).toBe("<body")
  })

  it('test-2', () => {
    let str = "<!DOCTYPE><html><body><i>abc<b>xxx</b></i></body></html>"
    expect(html2Md(str)).toBe("*abc**xxx***")
  })

  it('test-3', () => {
    let str = "<pre class=\"hljs language-md\"><code><span class=\"hljs-bullet\"> - </span>foo\n" +
      "<span class=\"hljs-bullet\">\n" +
      " - </span>bar\n" +
      "<span class=\"hljs-bullet\"> - </span>baz\n" +
      "</code></pre>"
    expect(html2Md(str)).toBe('```md\n' +
      ' - foo\n' +
      '\n' +
      ' - bar\n' +
      ' - baz\n' +
      '```')
  })


  it('pre code and p', () => {
    let str = '<ul>\n' +
      '<li>\n' +
      '<p><strong>Since version 1.4.0, showdown supports the markdown="1" attribute</strong>, but for older versions, this attribute is ignored. This means:</p>\n' +
      '<pre><code>  &lt;div markdown="1"&gt;\n' +
      '       Markdown does *not* work in here.\n' +
      '  &lt;/div&gt;\n' +
      '</code></pre>\n' +
      '</li>\n' +
      '<li>\n' +
      '<p>You can only nest square brackets in link titles to a depth of two levels:</p>\n' +
      '<pre><code>  [[fine]](http://www.github.com/)\n' +
      '  [[[broken]]](http://www.github.com/)\n' +
      '</code></pre>\n' +
      '<p>If you need more, you can escape them with backslashes.</p>\n' +
      '</li>\n' +
      '<li>\n' +
      '<p>A list is <strong>single paragraph</strong> if it has only <strong>1 line-break separating items</strong> and it becomes <strong>multi paragraph if ANY of its items is separated by 2 line-breaks</strong>:</p>\n' +
      '<pre class="hljs language-md"><code><span class="hljs-bullet"> - </span>foo\n' +
      '<span class="hljs-bullet">\n' +
      ' - </span>bar\n' +
      '<span class="hljs-bullet"> - </span>baz\n' +
      '</code></pre>\n' +
      '<p>becomes</p>\n' +
      '<pre class="hljs language-html"><code><span class="hljs-tag">&lt;<span class="hljs-name">ul</span>&gt;</span>\n' +
      '  <span class="hljs-tag">&lt;<span class="hljs-name">li</span>&gt;</span><span class="hljs-tag">&lt;<span class="hljs-name">p</span>&gt;</span>foo<span class="hljs-tag">&lt;/<span class="hljs-name">p</span>&gt;</span><span class="hljs-tag">&lt;/<span class="hljs-name">li</span>&gt;</span>\n' +
      '  <span class="hljs-tag">&lt;<span class="hljs-name">li</span>&gt;</span><span class="hljs-tag">&lt;<span class="hljs-name">p</span>&gt;</span>bar<span class="hljs-tag">&lt;/<span class="hljs-name">p</span>&gt;</span><span class="hljs-tag">&lt;/<span class="hljs-name">li</span>&gt;</span>\n' +
      '  <span class="hljs-tag">&lt;<span class="hljs-name">li</span>&gt;</span><span class="hljs-tag">&lt;<span class="hljs-name">p</span>&gt;</span>baz<span class="hljs-tag">&lt;/<span class="hljs-name">p</span>&gt;</span><span class="hljs-tag">&lt;/<span class="hljs-name">li</span>&gt;</span>\n' +
      '<span class="hljs-tag">&lt;/<span class="hljs-name">ul</span>&gt;</span>\n' +
      '</code></pre>\n' +
      '</li>\n' +
      '</ul>'
    expect(html2Md(str)).toBe("* **Since version 1.4.0, showdown supports the markdown=\"1\" attribute**, but for older versions, this attribute is ignored. This means:\n" +
        "\n" +
        "  ```\n" +
        "    <div markdown=\"1\">\n" +
        "         Markdown does *not* work in here.\n" +
        "    </div>\n" +
        "  ```\n" +
        "\n" +
        "* You can only nest square brackets in link titles to a depth of two levels:\n" +
        "\n" +
        "  ```\n" +
        "    [[fine]](http://www.github.com/)\n" +
        "    [[[broken]]](http://www.github.com/)\n" +
        "  ```\n" +
        "\n" +
        "  If you need more, you can escape them with backslashes.\n" +
        "\n" +
        "* A list is **single paragraph** if it has only **1 line-break separating items** and it becomes **multi paragraph if ANY of its items is separated by 2 line-breaks**:\n" +
        "\n" +
        "  ```md\n" +
        "   - foo\n" +
        "\n" +
        "   - bar\n" +
        "   - baz\n" +
        "  ```\n" +
        "\n" +
        "  becomes\n" +
        "\n" +
        "  ```html\n" +
        "  <ul>\n" +
        "    <li><p>foo</p></li>\n" +
        "    <li><p>bar</p></li>\n" +
        "    <li><p>baz</p></li>\n" +
        "  </ul>\n" +
        "  ```")
  })


  it('li child has p', () => {
    let str = "<ul>\n" +
      "<li>\n" +
      "<p>rawgit CDN</p>\n" +
      "<pre><code>  https://cdn.rawgit.com/showdownjs/showdown/&lt;version tag&gt;/dist/showdown.min.js\n" +
      "</code></pre>\n" +
      "</li>\n" +
      "<li>\n" +
      "<p>cdnjs</p>\n" +
      "<pre><code>  https://cdnjs.cloudflare.com/ajax/libs/showdown/&lt;version tag&gt;/showdown.min.js\n" +
      "</code></pre>\n" +
      "</li>\n" +
      "</ul>"
    expect(html2Md(str)).toBe("* rawgit CDN\n" +
        "\n" +
        "  ```\n" +
        "    https://cdn.rawgit.com/showdownjs/showdown/<version tag>/dist/showdown.min.js\n" +
        "  ```\n" +
        "\n" +
        "* cdnjs\n" +
        "\n" +
        "  ```\n" +
        "    https://cdnjs.cloudflare.com/ajax/libs/showdown/<version tag>/showdown.min.js\n" +
        "  ```")
  })

  it(" ``` inside <code></code>, should be nest", () => {
    let str = '<h3>Multiple lines</h3>\n' +
      '<p>To create blocks of code you should indent it by four spaces.</p>\n' +
      '<pre class="hljs language-md"><code><span class="hljs-code">    this is a piece</span>\n' +
      '<span class="hljs-code">    of</span>\n' +
      '<span class="hljs-code">    code</span>\n' +
      '</code></pre>\n' +
      '<p>If the options <strong><code>ghCodeBlocks</code></strong> is activated (which is by default), you can use triple backticks (```) to format text as its own distinct block.</p>\n' +
      '<pre><code>Check out this neat program I wrote:\n' +
      '\n' +
      '```\n' +
      'x = 0\n' +
      'x = 2 + 2\n' +
      'what is x\n' +
      '```\n' +
      '</code></pre>\n'
    expect(html2Md(str)).toBe('### Multiple lines\n' +
      '\n' +
      'To create blocks of code you should indent it by four spaces.\n' +
      '\n' +
      '```md\n' +
      '    this is a piece\n' +
      '    of\n' +
      '    code\n' +
      '```\n' +
      '\n' +
      'If the options **`ghCodeBlocks`** is activated (which is by default), you can use triple backticks (\\`\\`\\`) to format text as its own distinct block.\n' +
      '\n' +
      '    Check out this neat program I wrote:\n' +
      '\n' +
      '    ```\n' +
      '    x = 0\n' +
      '    x = 2 + 2\n' +
      '    what is x\n' +
      '    ```')
  })

  it('multi nest p', () => {
    expect(html2Md('<ul>\n<li>\n<p>p-1</p>\n<p>p-2</p>\n</li>\n<li>\n<p>p-3</p>\n<p>p-4</p>\n</li>\n</ul>'))
    .toBe("* p-1\n" +
        "\n" +
        "  p-2\n" +
        "\n" +
        "* p-3\n" +
        "\n" +
        "  p-4")
  })

  it(" ``` in complicate list", () => {
    expect(html2Md('<ul>\n' +
      '<li>a</li>\n' +
      '<li>b\n' +
      '<ul>\n' +
      '<li>\n' +
      '<p>code</p>\n' +
      '<pre><code>```javascript\n' +
      'function\n' +
      '```\n' +
      '</code></pre>\n' +
      '</li>\n' +
      '</ul>\n' +
      '</li>\n' +
      '<li>c</li>\n' +
      '</ul>'))
      .toBe("* a\n" +
          "* b\n" +
          "  * code\n" +
          "\n" +
          "        ```javascript\n" +
          "        function\n" +
          "        ```\n" +
          "* c")
  })

  it(" ``` in blockquote", () => {
    expect(html2Md('<blockquote>\n' +
      '<p>sdfsdfsf</p>\n' +
      '<blockquote>\n' +
      '<p>sdfsf</p>\n' +
      '<blockquote>\n' +
      '<p><code>fsdf</code></p>\n' +
      '<pre><code>```sdfsdfsdf```\n' +
      'this is function</code></pre>\n' +
      '</blockquote>\n' +
      '</blockquote>\n' +
      '</blockquote>'))
      .toBe("> sdfsdfsf\n" +
          ">\n" +
          ">> sdfsf\n" +
          ">>\n" +
          ">>> `fsdf`\n" +
          ">>>\n" +
          ">>>     ```sdfsdfsdf```\n" +
          ">>>     this is function")
  })

  it(" ``` in list without <p>", () => {
    expect(html2Md('<ul>\n' +
      '<li>\n' +
      '<pre><code>```\n' +
      'var a=5\n' +
      '```</code></pre>\n' +
      '</li>\n' +
      '</ul>\n'))
      .toBe("*     ```\n" +
          "      var a=5\n" +
          "      ```")
  })

  it(" multi nest code", () => {
    expect(html2Md('<ul>\n' +
      '<li>c\n' +
      '<ul>\n' +
      '<li>d\n' +
      '<ul>\n' +
      '<li>\n' +
      '<pre class="hljs"><code>abc\n' +
      '</code></pre>\n' +
      '</li>\n' +
      '</ul>\n' +
      '</li>\n' +
      '</ul>\n' +
      '</li>\n' +
      '</ul>'))
      .toBe("* c\n" +
          "  * d\n" +
          "    * ```\n" +
          "      abc\n" +
          "      ```")
  })

  it(" multi nest code2", () => {
    expect(html2Md('<ul>\n' +
      '<li>c\n' +
      '<ul>\n' +
      '<li>d\n' +
      '<ul>\n' +
      '<li>\n' +
      '<pre><code>```\n' +
      '</code></pre>\n' +
      'abc<pre class="hljs"><code></code></pre>\n' +
      '</li>\n' +
      '</ul>\n' +
      '</li>\n' +
      '</ul>\n' +
      '</li>\n' +
      '</ul>'))
      .toBe("* c\n" +
          "  * d\n" +
          "    *     ```\n" +
          "\n" +
          "      abc\n" +
          "      ```\n" +
          "\n" +
          "      ```")
  })


  it('nest hr',()=>{
    expect(html2Md("<ol>\n" +
      "<li>sdff\n" +
      "<ol>\n" +
      "<li>sdfsf</li>\n" +
      "<li>\n" +
      "<hr>\n" +
      "<hr>\n" +
      "</li>\n" +
      "</ol>\n" +
      "</li>\n" +
      "</ol>\n")).toBe(
        "1. sdff\n" +
        "   1. sdfsf\n" +
        "   2. ---\n" +
        "\n" +
        "      ---")
  })
  it('slim hr',()=>{
    expect(html2Md('<hr>\n\n\n\n\n\n\n' +
      '<hr>\n\n\n\n\n\n\n' +
      '<hr>\n\n\n\n\n\n\n')).toBe('---\n' +
      '\n' +
      '---\n' +
      '\n' +
      '---')
  })
})



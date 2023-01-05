import html2Md from '../../src/index'

describe('module test1',()=>{
  it('test-1',()=>{
    let str="<p><strong>Advertisement 😃</strong></p>\n" +
      "<ul>\n" +
      "<li><strong><a href=\"https://nodeca.github.io/pica/demo/\">pica</a></strong> - high quality and fast image\n" +
      "resize in browser.</li>\n" +
      "<li><strong><a href=\"https://github.com/nodeca/babelfish/\">babelfish</a></strong> - developer friendly\n" +
      "i18n with plurals support and easy syntax.</li>\n" +
      "</ul>\n" +
      "<p>You will like those projects!</p>\n" +
      "<hr>\n" +
      "<h1>h1 Heading</h1>\n" +
      "<h2>h2 Heading</h2>\n" +
      "<h3>h3 Heading</h3>\n" +
      "<h4>h4 Heading</h4>\n" +
      "<h5>h5 Heading</h5>\n" +
      "<h6>h6 Heading</h6>\n" +
      "<h2>Horizontal Rules</h2>\n" +
      "<hr>\n" +
      "<hr>\n" +
      "<hr>\n" +
      "<h2>Typographic replacements</h2>\n" +
      "<p>Enable typographer option to see result.</p>\n" +
      "<p>© © ® ® ™ ™ § § ±</p>\n" +
      "<p>test… test… test… test?.. test!..</p>\n" +
      "<p>!!! ??? ,  – —</p>\n" +
      "<p>“Smartypants, double quotes” and ‘single quotes’</p>\n" +
      "<h2>Emphasis</h2>\n" +
      "<p><strong>This is bold text</strong></p>\n" +
      "<p><strong>This is bold text</strong></p>\n" +
      "<p><em>This is italic text</em></p>\n" +
      "<p><em>This is italic text</em></p>\n" +
      "<p><s>Strikethrough</s></p>\n" +
      "<h2>Blockquotes</h2>\n" +
      "<blockquote>\n" +
      "<p>Blockquotes can also be nested…</p>\n" +
      "<blockquote>\n" +
      "<p>…by using additional greater-than signs right next to each other…</p>\n" +
      "<blockquote>\n" +
      "<p>…or with spaces between arrows.</p>\n" +
      "</blockquote>\n" +
      "</blockquote>\n" +
      "</blockquote>\n" +
      "<h2>Lists</h2>\n" +
      "<p>Unordered</p>\n" +
      "<ul>\n" +
      "<li>Create a list by starting a line with <code>+</code>, <code>-</code>, or <code>*</code></li>\n" +
      "<li>Sub-lists are made by indenting 2 spaces:\n" +
      "<ul>\n" +
      "<li>Marker character change forces new list start:\n" +
      "<ul>\n" +
      "<li>Ac tristique libero volutpat at</li>\n" +
      "</ul>\n" +
      "<ul>\n" +
      "<li>Facilisis in pretium nisl aliquet</li>\n" +
      "</ul>\n" +
      "<ul>\n" +
      "<li>Nulla volutpat aliquam velit</li>\n" +
      "</ul>\n" +
      "</li>\n" +
      "</ul>\n" +
      "</li>\n" +
      "<li>Very easy!</li>\n" +
      "</ul>\n" +
      "<p>Ordered</p>\n" +
      "<ol>\n" +
      "<li>\n" +
      "<p>Lorem ipsum dolor sit amet</p>\n" +
      "</li>\n" +
      "<li>\n" +
      "<p>Consectetur adipiscing elit</p>\n" +
      "</li>\n" +
      "<li>\n" +
      "<p>Integer molestie lorem at massa</p>\n" +
      "</li>\n" +
      "<li>\n" +
      "<p>You can use sequential numbers…</p>\n" +
      "</li>\n" +
      "<li>\n" +
      "<p>…or keep all the numbers as <code>1.</code></p>\n" +
      "</li>\n" +
      "</ol>\n" +
      "<ol>\n" +
      "<li>\n" +
      "Lorem ipsum dolor sit amet\n" +
      "</li>\n" +
      "<li>\n" +
      "Consectetur adipiscing elit\n" +
      "</li>\n" +
      "<li>\n" +
      "Integer molestie lorem at massa\n" +
      "</li>\n" +
      "<li>\n" +
      "You can use sequential numbers…</li>\n" +
      "<li>\n" +
      "…or keep all the numbers as <code>1.</code>\n" +
      "</li>\n" +
      "</ol>\n" +
      "<p>Start numbering with offset:</p>\n" +
      "<ol start=\"57\">\n" +
      "<li>foo</li>\n" +
      "<li>bar</li>\n" +
      "</ol>\n" +
      "<h2>Code</h2>\n" +
      "<p>Inline <code>code</code></p>\n" +
      "<p>Indented code</p>\n" +
      "<pre><code>// Some comments\n" +
      "line 1 of code\n" +
      "line 2 of code\n" +
      "line 3 of code\n" +
      "</code></pre>\n" +
      "<p>Block code “fences”</p>\n" +
      "<pre class=\"hljs\"><code>Sample text here...\n" +
      "</code></pre>\n" +
      "<p>Syntax highlighting</p>\n" +
      "<pre class=\"hljs language-js\"><code><span class=\"hljs-keyword\">var</span> foo = <span class=\"hljs-function\"><span class=\"hljs-keyword\">function</span> (<span class=\"hljs-params\">bar</span>) </span>{\n" +
      "  <span class=\"hljs-keyword\">return</span> bar++;\n" +
      "};\n" +
      "\n" +
      "<span class=\"hljs-built_in\">console</span>.log(foo(<span class=\"hljs-number\">5</span>));\n" +
      "</code></pre>\n" +
      "<h2>Tables</h2>\n" +
      "<table class=\"table table-striped\">\n" +
      "<thead>\n" +
      "<tr>\n" +
      "<th>Option</th>\n" +
      "<th>Description</th>\n" +
      "</tr>\n" +
      "</thead>\n" +
      "<tbody>\n" +
      "<tr>\n" +
      "<td>data</td>\n" +
      "<td>path to data files to supply the data that will be passed into templates.</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td>engine</td>\n" +
      "<td>engine to be used for processing templates. Handlebars is the default.</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td>ext</td>\n" +
      "<td>extension to be used for dest files.</td>\n" +
      "</tr>\n" +
      "</tbody>\n" +
      "</table>\n" +
      "<p>Right aligned columns</p>\n" +
      "<table class=\"table table-striped\">\n" +
      "<thead>\n" +
      "<tr>\n" +
      "<th style=\"text-align:right\">Option</th>\n" +
      "<th style=\"text-align:right\">Description</th>\n" +
      "</tr>\n" +
      "</thead>\n" +
      "<tbody>\n" +
      "<tr>\n" +
      "<td style=\"text-align:right\">data</td>\n" +
      "<td style=\"text-align:right\">path to data files to supply the data that will be passed into templates.</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td style=\"text-align:right\">engine</td>\n" +
      "<td style=\"text-align:right\">engine to be used for processing templates. Handlebars is the default.</td>\n" +
      "</tr>\n" +
      "<tr>\n" +
      "<td style=\"text-align:right\">ext</td>\n" +
      "<td style=\"text-align:right\">extension to be used for dest files.</td>\n" +
      "</tr>\n" +
      "</tbody>\n" +
      "</table>\n" +
      "<h2>Links</h2>\n" +
      "<p><a href=\"http://dev.nodeca.com\">link text</a></p>\n" +
      "<p><a href=\"http://nodeca.github.io/pica/demo/\" title=\"title text!\">link with title</a></p>\n" +
      "<p>Autoconverted link <a href=\"https://github.com/nodeca/pica\">https://github.com/nodeca/pica</a> (enable linkify to see)</p>\n" +
      "<h2>Images</h2>\n" +
      "<p><img src=\"https://octodex.github.com/images/minion.png\" alt=\"Minion\">\n" +
      "<img src=\"https://octodex.github.com/images/stormtroopocat.jpg\" alt=\"Stormtroopocat\" title=\"The Stormtroopocat\"></p>\n" +
      "<p>Like links, Images also have a footnote style syntax</p>\n" +
      "<p><img src=\"https://octodex.github.com/images/dojocat.jpg\" alt=\"Alt text\" title=\"The Dojocat\"></p>\n" +
      "<p>With a reference later in the document defining the URL location:</p>\n" +
      "<h2>Plugins</h2>\n" +
      "<p>The killer feature of <code>markdown-it</code> is very effective support of\n" +
      "<a href=\"https://www.npmjs.org/browse/keyword/markdown-it-plugin\">syntax plugins</a>.</p>\n" +
      "<h3><a href=\"https://github.com/markdown-it/markdown-it-emoji\">Emojies</a></h3>\n" +
      "<blockquote>\n" +
      "</blockquote>\n" +
      "<p>see <a href=\"https://github.com/markdown-it/markdown-it-emoji#change-output\">how to change output</a> with twemoji.</p>\n" +
      "<h3><a href=\"https://github.com/markdown-it/markdown-it-sub\">Subscript</a> / <a href=\"https://github.com/markdown-it/markdown-it-sup\">Superscript</a></h3>\n" +
      "<ul>\n" +
      "<li>19<sup>th</sup></li>\n" +
      "<li>H<sub>2</sub>O</li>\n" +
      "</ul>\n" +
      "<h3><a href=\"https://github.com/markdown-it/markdown-it-footnote\">Footnotes</a></h3>\n" +
      "<p>Footnote 1 link<sup><a href=\"#fn1\">[1]</a></sup>.</p>\n" +
      "<p>Footnote 2 link<sup><a href=\"#fn2\">[2]</a></sup>.</p>\n" +
      "<p>Inline footnote<sup><a href=\"#fn3\">[3]</a></sup> definition.</p>\n" +
      "<p>Duplicated footnote reference<sup><a href=\"#fn2\">[2:1]</a></sup>.</p>\n" +
      "<p><em>here be dragons</em></p>\n"+
      "<h2 id=\"todo-list\">Todo list</h2>\n" +
      "<ul>\n" +
      "<li><input disabled=\"\" type=\"checkbox\"> not finish-1</li>\n" +
      "<li><input disabled=\"\" type=\"checkbox\"> not finish-2</li>\n" +
      "<li><input disabled=\"\" type=\"checkbox\"> not finish-3</li>\n" +
      "<li><input disabled=\"\" type=\"checkbox\"> not finish-4</li>\n" +
      "</ul>\n" +
      "<h2 id=\"done-list\">Done list</h2>\n" +
      "<ul>\n" +
      "<li><input checked=\"\" disabled=\"\" type=\"checkbox\"> finish-1</li>\n" +
      "<li><input checked=\"\" disabled=\"\" type=\"checkbox\"> finish-2</li>\n" +
      "<li><input checked=\"\" disabled=\"\" type=\"checkbox\"> finish-3</li>\n" +
      "<li><input checked=\"\" disabled=\"\" type=\"checkbox\"> finish-4</li>\n" +
      "</ul>"

    expect(html2Md(str)).toBe('**Advertisement 😃**\n' +
      '\n' +
      '* **[pica](https://nodeca.github.io/pica/demo/)** - high quality and fast image resize in browser.\n' +
      '* **[babelfish](https://github.com/nodeca/babelfish/)** - developer friendly i18n with plurals support and easy syntax.\n' +
      '\n' +
      'You will like those projects!\n' +
      '\n' +
      '---\n' +
      '\n' +
      '# h1 Heading\n' +
      '\n' +
      '## h2 Heading\n' +
      '\n' +
      '### h3 Heading\n' +
      '\n' +
      '#### h4 Heading\n' +
      '\n' +
      '##### h5 Heading\n' +
      '\n' +
      '###### h6 Heading\n' +
      '\n' +
      '## Horizontal Rules\n' +
      '\n' +
      '---\n' +
      '\n' +
      '---\n' +
      '\n' +
      '---\n' +
      '\n' +
      '## Typographic replacements\n' +
      '\n' +
      'Enable typographer option to see result.\n' +
      '\n' +
      '© © ® ® ™ ™ § § ±\n' +
      '\n' +
      'test… test… test… test?.. test!..\n' +
      '\n' +
      '!!! ??? , – —\n' +
      '\n' +
      '“Smartypants, double quotes” and ‘single quotes’\n' +
      '\n' +
      '## Emphasis\n' +
      '\n' +
      '**This is bold text**\n' +
      '\n' +
      '**This is bold text**\n' +
      '\n' +
      '*This is italic text*\n' +
      '\n' +
      '*This is italic text*\n' +
      '\n' +
      '~~Strikethrough~~\n' +
      '\n' +
      '## Blockquotes\n' +
      '\n' +
      '> Blockquotes can also be nested…\n' +
      '>\n' +
      '>> …by using additional greater-than signs right next to each other…\n' +
      '>>\n' +
      '>>> …or with spaces between arrows.\n' +
      '\n' +
      '## Lists\n' +
      '\n' +
      'Unordered\n' +
      '\n' +
      '* Create a list by starting a line with `+`, `-`, or `*`\n' +
      '* Sub-lists are made by indenting 2 spaces:\n' +
      '  * Marker character change forces new list start:\n' +
      '    * Ac tristique libero volutpat at\n' +
      '\n' +
      '    * Facilisis in pretium nisl aliquet\n' +
      '\n' +
      '    * Nulla volutpat aliquam velit\n' +
      '* Very easy!\n' +
      '\n' +
      'Ordered\n' +
      '\n' +
      '1. Lorem ipsum dolor sit amet\n' +
      '\n' +
      '2. Consectetur adipiscing elit\n' +
      '\n' +
      '3. Integer molestie lorem at massa\n' +
      '\n' +
      '4. You can use sequential numbers…\n' +
      '\n' +
      '5. …or keep all the numbers as `1.`\n' +
      '\n' +
      '1. Lorem ipsum dolor sit amet\n' +
      '2. Consectetur adipiscing elit\n' +
      '3. Integer molestie lorem at massa\n' +
      '4. You can use sequential numbers…\n' +
      '5. …or keep all the numbers as `1.`\n' +
      '\n' +
      'Start numbering with offset:\n' +
      '\n' +
      '57. foo\n' +
      '58. bar\n' +
      '\n' +
      '## Code\n' +
      '\n' +
      'Inline `code`\n' +
      '\n' +
      'Indented code\n' +
      '\n' +
      '```\n' +
      '// Some comments\n' +
      'line 1 of code\n' +
      'line 2 of code\n' +
      'line 3 of code\n' +
      '```\n' +
      '\n' +
      'Block code “fences”\n' +
      '\n' +
      '```\n' +
      'Sample text here...\n' +
      '```\n' +
      '\n' +
      'Syntax highlighting\n' +
      '\n' +
      '```js\n' +
      'var foo = function (bar) {\n' +
      '  return bar++;\n' +
      '};\n' +
      '\n' +
      'console.log(foo(5));\n' +
      '```\n' +
      '\n' +
      '## Tables\n' +
      '\n' +
      '|Option|Description|\n' +
      '|---|---|\n' +
      '|data|path to data files to supply the data that will be passed into templates.|\n' +
      '|engine|engine to be used for processing templates. Handlebars is the default.|\n' +
      '|ext|extension to be used for dest files.|\n' +
      '\n' +
      'Right aligned columns\n' +
      '\n' +
      '|Option|Description|\n' +
      '|---:|---:|\n' +
      '|data|path to data files to supply the data that will be passed into templates.|\n' +
      '|engine|engine to be used for processing templates. Handlebars is the default.|\n' +
      '|ext|extension to be used for dest files.|\n' +
      '\n' +
      '## Links\n' +
      '\n' +
      '[link text](http://dev.nodeca.com)\n' +
      '\n' +
      '[link with title](http://nodeca.github.io/pica/demo/ "title text!")\n' +
      '\n' +
      'Autoconverted link [https://github.com/nodeca/pica](https://github.com/nodeca/pica) (enable linkify to see)\n' +
      '\n' +
      '## Images\n' +
      '\n' +
      '![Minion](https://octodex.github.com/images/minion.png) ![Stormtroopocat](https://octodex.github.com/images/stormtroopocat.jpg)\n' +
      '\n' +
      'Like links, Images also have a footnote style syntax\n' +
      '\n' +
      '![Alt text](https://octodex.github.com/images/dojocat.jpg)\n' +
      '\n' +
      'With a reference later in the document defining the URL location:\n' +
      '\n' +
      '## Plugins\n' +
      '\n' +
      'The killer feature of `markdown-it` is very effective support of [syntax plugins](https://www.npmjs.org/browse/keyword/markdown-it-plugin).\n' +
      '\n' +
      '### [Emojies](https://github.com/markdown-it/markdown-it-emoji)\n' +
      '\n' +
      'see [how to change output](https://github.com/markdown-it/markdown-it-emoji#change-output) with twemoji.\n' +
      '\n' +
      '### [Subscript](https://github.com/markdown-it/markdown-it-sub) / [Superscript](https://github.com/markdown-it/markdown-it-sup)\n' +
      '\n' +
      '* 19<sup>th</sup>\n' +
      '* H<sub>2</sub>O\n' +
      '\n' +
      '### [Footnotes](https://github.com/markdown-it/markdown-it-footnote)\n' +
      '\n' +
      'Footnote 1 link<sup>[\\[1\\]](#fn1)</sup>.\n' +
      '\n' +
      'Footnote 2 link<sup>[\\[2\\]](#fn2)</sup>.\n' +
      '\n' +
      'Inline footnote<sup>[\\[3\\]](#fn3)</sup> definition.\n' +
      '\n' +
      'Duplicated footnote reference<sup>[\\[2:1\\]](#fn2)</sup>.\n' +
      '\n' +
      '*here be dragons*\n' +
      '\n' +
      '## Todo list\n' +
      '\n' +
      '* [ ]  not finish-1\n' +
      '* [ ]  not finish-2\n' +
      '* [ ]  not finish-3\n' +
      '* [ ]  not finish-4\n' +
      '\n' +
      '## Done list\n' +
      '\n' +
      '* [x]  finish-1\n' +
      '* [x]  finish-2\n' +
      '* [x]  finish-3\n' +
      '* [x]  finish-4')
  })

  it('input without li parent,  not render',()=>{
    let str='<input type="checkbox" checked disabled />\n<input type="checkbox" disabled />'
    expect(html2Md(str)).toBe('')
  })
})

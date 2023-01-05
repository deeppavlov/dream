import P from '../../src/tags/p'
import html2Md from '../../src/index'
describe('Remove some space',()=>{


  it('The space between tags should be remove',()=>{
    let spaceHtml=new P("<p>       <strong>strong</strong></p>")
    expect(spaceHtml.exec()).toBe("\n" +
      "**strong**\n")
  })

  it('The space between tags should be remove 2',()=>{
    let spaceHtml=html2Md("<div id=\"breadcrumbs\" class=\"clearfix\">\n" +
      "  <ul class=\"breadcrumbs-container\">\n" +
      "    <li><a href=\"index.html\">PHP Manual</a></li>\n" +
      "    <li><a href=\"class.apciterator.html\">APCIterator</a></li>\n" +
      "    <li>Constructs an APCIterator iterator object</li>\n" +
      "  </ul>\n" +
      "</div>\n" +
      "<div>\n" +
      "  <div>\n" +
      " <div>\n" +
      "  <h1>APCIterator::__construct</h1>\n" +
      " </div></div></div></div>")
    expect(spaceHtml).toBe(
      "* [PHP Manual](index.html)\n" +
      "* [APCIterator](class.apciterator.html)\n" +
      "* Constructs an APCIterator iterator object\n" +
      "\n" +
      "# APCIterator::\\_\\_construct")
  })
})

import Tag from "../../src/Tag";
import SelfCloseTag from "../../src/SelfCloseTag";
import html2Md from '../../src/index'

describe('error test', () => {

  it('not integrity test', () => {
    let str='</ol>\n' +
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
      '</li>'

    expect(html2Md(str)).toBe(
        '> 1. bq-nest-2\n' +
        '>\n' +
        '>> 1. bq-nest-3')
  })

  it('unvalid tag, string, not close, wrong tagname, self tag in Tag', () => {
    let str='String send inside Tag'
    let str2='<b>String send inside Tag'
    let str3='<img src="some.jpg" />'
    let str4='<div data-attr="some-attr" />'
    let str5='<div data-attr="some-attr" >'
    let tag=new Tag(str)
    let tag2=new Tag(str2, 'a')
    let tag3=new Tag(str3, 'img')
    let tag4=new Tag(str4, 'div')
    let tag5=new Tag(str5, 'div')
    expect(tag.innerHTML).toBe('')
    expect(tag2.innerHTML).toBe('')
    expect(tag3.innerHTML).toBe('')
    expect(tag4.innerHTML).toBe('')
    expect(tag5.innerHTML).toBe('')
  })


  it('unvalid selfTag, string, wrong tagName in SelfCloseTag ', () => {
    let str='String send inside selfTag'
    let str2='<img src="some.jpg" />'
    let selfTag=new SelfCloseTag(str)
    let selfTag2=new SelfCloseTag(str2,'input')
    expect(selfTag.attrs).toEqual({})
    expect(selfTag2.attrs).toEqual({})
  })

  it('other tags inside tr', () => {
    let str="<table>\n" +
        "\n" +
        "<thead>\n" +
        "<tr>\n" +
        "<p>data-1-left</p>\n" +
        "<th>data-1-center</th>\n" +
        "</tr>\n" +
        "</thead>\n" +
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
        "</table>"
    expect(html2Md(str)).toBe('|data-1-center|\n' +
        '|---|\n' +
        '|data-1-left|data-1-center|\n' +
        '|data-2-left|data-2-center|\n' +
        '|data-3-left|data-3-center|')
  })

  it('Not valid p in Ol',()=>{
    let str='<ol>\n' +
        '<li>one</li>\n' +
        '<p>two</p>\n' +
        '<li>three</li>\n' +
        '</ol>'
    expect(html2Md(str)).toBe('1. one\n' +
        '2. three')
  })

  it('Not valid p in Ol2',()=>{
    let str='<ol>\n' +
        '<li>one</li>\n' +
        '<b>two</b>\n' +
        '<li>three</li>\n' +
        '</ol>'
    expect(html2Md(str)).toBe('1. one\n' +
        '2. three')
  })

  it('Not valid tag in Ul',()=>{
    let str='<ul>\n' +
        '<li>one</li>\n' +
        '<b>two</b>\n' +
        '<li>three</li>\n' +
        '</ul>'
    expect(html2Md(str)).toBe('* one\n' +
        '* three')
  })
})



import html2Md from '../../src/index'
import {tagSpaceNum} from '../options'

describe("test <blockquote></blockquote> tag",()=>{

  it('no nest',()=>{
    let blockquote=html2Md("<blockquote>\n" +
      "<p>This is <strong>quote</strong>…</p>\n" +
      "</blockquote>")
    expect(blockquote).toBe(
      "> This is **quote**…")
  })


  it('nest ul',()=>{
    let blockquote=html2Md("<blockquote>\n" +
      "<ul>\n" +
      "<li>sdfs</li>\n" +
      "<li>sdfsdf</li>\n" +
      "<li>sdfsaf</li>\n" +
      "</ul>\n" +
      "</blockquote>")
    expect(blockquote).toBe(
        "> * sdfs\n" +
        "> * sdfsdf\n" +
        "> * sdfsaf")
  })

  it('nest blockquote',()=>{
    let blockquote=html2Md("<blockquote>\n" +
      "<p>Blockquotes can also be nested…</p>\n" +
      "<blockquote>\n" +
      "<p>…by using additional greater-than signs right next to each other…</p>\n" +
      "<blockquote>\n" +
      "<p>…or with spaces between arrows.</p>\n" +
      "</blockquote>\n" +
      "</blockquote>\n" +
      "</blockquote>")

    expect(blockquote).toBe(
      "> Blockquotes can also be nested…\n" +
      ">\n" +
      ">> …by using additional greater-than signs right next to each other…\n" +
      ">>\n" +
      ">>> …or with spaces between arrows.")
  })

  it('some independent line tag in blockquote',()=>{
    let blockquote=html2Md("<blockquote>\n" +
        "<p>Blockquotes can also be nested…</p>\n" +
        "<blockquote>\n" +
        "<p>…by using additional greater-than signs right next to each other…</p>\n" +
        "<blockquote>\n" +
        "<p>…or with spaces between arrows.</p>\n" +
        "</blockquote>\n" +
        "</blockquote>\n" +
        "</blockquote>")

    expect(blockquote).toBe(
        "> Blockquotes can also be nested…\n" +
        ">\n" +
        ">> …by using additional greater-than signs right next to each other…\n" +
        ">>\n" +
        ">>> …or with spaces between arrows.")
  })

  it('some independent line tag in blockquote 2',()=>{
    let blockquote=html2Md("<blockquote>主题: React\n" +
        "        <br>\n" +
        "        难度: <del>ddd</del>\n" +
        "        <p>paragraph1</p>\n" +
        "        raw text1<b>bold</b>\n" +
        "        <p>paragraph2</p>\n" +
        "    </blockquote>")

    expect(blockquote).toBe("> 主题: React  \n" +
        "> 难度: ~~ddd~~\n" +
        ">\n" +
        "> paragraph1\n" +
        ">\n" +
        "> raw text1**bold**\n" +
        ">\n" +
        "> paragraph2")
  })

  it('multiple br in blockquote',()=>{
    let blockquote=html2Md("<blockquote>主题: React\n" +
        "        <br><br><br>\n" +
        "        难度: <del>ddd</del>\n" +
        "        <p>paragraph1</p>\n" +
        "        raw text1<b>bold</b>\n" +
        "        <p>paragraph2</p>\n" +
        "    </blockquote>")

    expect(blockquote).toBe("> 主题: React  \n" +
        ">   \n" +
        ">   \n" +
        "> 难度: ~~ddd~~\n" +
        ">\n" +
        "> paragraph1\n" +
        ">\n" +
        "> raw text1**bold**\n" +
        ">\n" +
        "> paragraph2")
  })
})


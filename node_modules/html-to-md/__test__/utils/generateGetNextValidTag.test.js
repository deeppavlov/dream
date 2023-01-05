import { generateGetNextValidTag } from '../../src/utils'


describe('测试寻找标签',()=>{

  it('Normal tags',()=>{
    let findFunc=generateGetNextValidTag('<div>abc</div>')
    expect(findFunc()).toStrictEqual(["div", "<div>abc</div>"])
  })

  it('Have sub tags',()=>{
    expect(generateGetNextValidTag('<div><b>Strong</b></div>')()).toStrictEqual(["div", "<div><b>Strong</b></div>"])
  })

  it('Self close tag',()=>{
    expect(generateGetNextValidTag('<img src="xxxx.png" />')()).toStrictEqual(["img", "<img src=\"xxxx.png\" />"])
  })

  it('Self close tag2',()=>{
    expect(generateGetNextValidTag('<img src="xxxx.png" >')()).toStrictEqual(["img", "<img src=\"xxxx.png\" >"])
  })

  it('No tags',()=>{
    expect(generateGetNextValidTag('xabc content text only')()).toStrictEqual([null,"xabc content text only"])
  })

  it('Have < in content',()=>{
    expect(generateGetNextValidTag('<cont<ent<content<')()).toStrictEqual([null, "<cont<ent<content<"])
  })

  it('Have < && > in content',()=>{
    expect(generateGetNextValidTag('<con>t<ent<con>tent<')()).toStrictEqual([null, "<con>t<ent<con>tent<"])
  })

  it('Unvalid tag',()=>{
    expect(generateGetNextValidTag('<div>abc</b>')()).toStrictEqual([null, "abc"])
  })
  it('Unvalid tag with valid sub tags',()=>{
    expect(generateGetNextValidTag('<div><i>italy</i><strong>Strong</strong></b>')()).toStrictEqual([null,'<i>italy</i><strong>Strong</strong>'])
  })

  it('Unvalid tag with valid sub tags with SPACE',()=>{
    expect(generateGetNextValidTag('<div><i>italy</i><strong>Strong</strong></b>')()).toStrictEqual([null,'<i>italy</i><strong>Strong</strong>'])
  })

  it('Multi tags',()=>{
    expect(generateGetNextValidTag(`<span>dfaf</span><a href=\"https://github.com/nodeca/babelfish/\"><i>babelfish</i></a>`)()).toStrictEqual(["span", "<span>dfaf</span>"])
  })

  it('some test',()=>{
    expect(generateGetNextValidTag("<div>ssss<divvvvvvvv</div>")()).toStrictEqual(["div", "<div>ssss<divvvvvvvv</div>"])
  })

  it('tags with -',()=>{
    expect(generateGetNextValidTag("<ab-cd>ssss</ab-cd>")()).toStrictEqual(["ab-cd", "<ab-cd>ssss</ab-cd>"])
  })
})

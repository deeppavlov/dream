import html2Md from '../../src/index'

describe('test special', () => {

  it('h1 Text should be next line', () => {
    let str = `<ul>
<li>
<h1>h1</h1>Should Be Next Line</li>
</ul>`
    expect(html2Md(str)).toBe(
        '* # h1\n' +
        '  Should Be Next Line')
  })

  it('h3 Text should be next line', () => {
    let str = `<ul>
<li>
<h3>h3</h3>Should Be Next Line</li>
</ul>`
    expect(html2Md(str)).toBe(
        '* ### h3\n' +
        '  Should Be Next Line')
  })

  it('Unvalid tag with valid sub tags',()=>{
    expect(html2Md('<div><i>italy</i><strong>Strong</strong></b>')).toBe("<i>italy</i><strong>Strong</strong>")
  })

  it('Unvalid tag in table',()=>{
    expect(html2Md('<table>\n' +
      '<tr><td>sdfdfdfdfdf<tdfdfdfdfdfd</td></tr>\n' +
      '</table>')).toBe(
      "||\n" +
      "|---|\n" +
      "|sdfdfdfdfdf<tdfdfdfdfdfd|")
  })

  it('Unvalid tag in normal tag',()=>{
    expect(html2Md("<b>sdfsdfs</b>dfsdf</b>")).toBe("**sdfsdfs**dfsdf")
  })

})



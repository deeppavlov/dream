import H3 from '../../src/tags/h3'


describe('test <h3></h3> tag',()=>{
  it('no nest',()=>{
    let h3=new H3("<h3>javascript</h3>")
    expect(h3.exec()).toBe("\n### javascript\n")
  })

  it('can nest',()=>{
    let h3=new H3("<h3><strong><i>strong and italic</i></strong></h3>")
    expect(h3.exec()).toBe("\n### ***strong and italic***\n")
  })

  it('can nest-2',()=>{
    let h3=new H3("<h3 class=\"line\" data-line=\"174\"><a href=\"https://github.com/markdown-it/markdown-it-sub\">Subscript</a> / <a href=\"https://github.com/markdown-it/markdown-it-sup\">Superscript</a></h3>")
    expect(h3.exec()).toBe("\n" +
      "### [Subscript](https://github.com/markdown-it/markdown-it-sub) / [Superscript](https://github.com/markdown-it/markdown-it-sup)\n")
  })
})

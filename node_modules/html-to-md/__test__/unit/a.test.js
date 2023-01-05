import A from '../../src/tags/a'

describe('test <a></a> tag',()=>{
  it('has href',()=>{
    let a=new A("<a href=\"https://nodeca.github.io/pica/demo/\"><strong>pica</strong></a>")
    expect(a.exec()).toBe("[**pica**](https://nodeca.github.io/pica/demo/)")
  })
  it('no href',()=>{
    let a=new A("<a><strong>pica</strong></a>")
    expect(a.exec()).toBe("[**pica**]()")
  })

  it('space and \n in tag',()=>{
    let a=new A(
`<a href="#">
    click
</a>`)
    expect(a.exec()).toBe('[click](#)')
  })

  it('space and \n in attributes',()=>{
    let a=new A(
`<a href="/#you-should-see-this"
data-moz-do-not-send="true">link from moz</a>`)
    expect(a.exec()).toBe("[link from moz](/#you-should-see-this)")
  })

  it('title in tag',()=>{
    let a=new A(`<a href="/#you-should-see-this" title="some title">link from moz</a>`)
    expect(a.exec()).toBe(`[link from moz](/#you-should-see-this "some title")`)
  })
})

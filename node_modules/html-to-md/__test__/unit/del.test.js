import Del from '../../src/tags/del'


describe('test <del></del> tag',()=>{
  it('no nest',()=>{
    let del=new Del("<del>javascript</del>")
    expect(del.exec()).toBe("~~javascript~~")
  })

  it('can nest',()=>{
    let del=new Del("<del><a href=\"https://github.com/nodeca/babelfish/\"><i>babelfish</i></a></del>")
    expect(del.exec()).toBe("~~[*babelfish*](https://github.com/nodeca/babelfish/)~~")
  })

  it('换行需省略',()=>{
    let del=new Del("<del>\n" +
      "<a href=\"https://github.com/nodeca/babelfish/\"><i>babelfish</i></a>\n" +
      "</del>")
    expect(del.exec()).toBe("~~[*babelfish*](https://github.com/nodeca/babelfish/)~~")
  })
})

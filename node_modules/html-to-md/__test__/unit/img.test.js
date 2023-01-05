import Img from '../../src/tags/img'


describe('test <img /> tag',()=>{
  it('has alt',()=>{
    let img=new Img("<img src=\"https://octodex.github.com/images/minion.png\" alt=\"Minion\">")
    expect(img.exec()).toBe("![Minion](https://octodex.github.com/images/minion.png)")
  })

  it('no alt',()=>{
    let img=new Img("<img src=\"https://octodex.github.com/images/minion.png\" >")
    expect(img.exec()).toBe("![](https://octodex.github.com/images/minion.png)")
  })

  it('empty alt',()=>{
    let img=new Img("<img src=\"https://octodex.github.com/images/minion.png\" alt=\"\">")
    expect(img.exec()).toBe("![](https://octodex.github.com/images/minion.png)")
  })

  it('= in attr value should keep',()=>{
    let img=new Img(`<img src="https://www.zhihu.com/equation?tex=A%5Cmathbf%7Bu%7D+%3D+%5Clambda%5Cmathbf%7Bu%7D%5C%5C" />`)
    expect(img.exec()).toBe('![](https://www.zhihu.com/equation?tex=A%5Cmathbf%7Bu%7D+%3D+%5Clambda%5Cmathbf%7Bu%7D%5C%5C)')
  })

  it(' " or \' in src value',()=>{
    let img=new Img(`<img src="http://abc'cde.png" />`)
    expect(img.exec()).toBe('![](http://abc\'cde.png)')
  })
})

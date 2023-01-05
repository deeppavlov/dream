import config from '../../src/config'

describe('跳过指定的tag标签，内部不影响',()=>{
  beforeEach(()=>{
    config.clear()
  })

  it('array，默认concat',()=>{
    config.set({a:[1,2]})
    config.set({a:[2,7]})
    expect(config.get()).toEqual({a:[1,2,2,7]})
  })

  it('array使用强制参数，则覆盖',()=>{
    config.set({a:[1,2]})
    config.set({a:[2,7]},true)
    expect(config.get()).toEqual({a:[2,7]})
  })

  it('obj，默认assign',()=>{
    config.set({a:{x:1,y:2}})
    config.set({a:{y:3,z:4}})
    expect(config.get()).toEqual({a:{x:1,y:3,z:4}})
  })

  it('引用值都只处理一层',()=>{
    config.set({a:{x:[1,2],y:[3,4]}})
    config.set({a:{y:[4,5],z:[6,7]}})
    expect(config.get()).toEqual({a:{x:[1,2],y:[4,5],z:[6,7]}})
  })

  it('obj使用强制参数，则覆盖',()=>{
    config.set({a:{x:1,y:2}})
    config.set({a:{y:3,z:4}},true)
    expect(config.get()).toEqual({a:{y:3,z:4}})
  })

  it('Number直接覆盖',()=>{
    config.set({a:1})
    config.set({a:5})
    expect(config.get()).toEqual({a:5})
  })

  it('String直接覆盖',()=>{
    config.set({a:'1'})
    config.set({a:'5'})
    expect(config.get()).toEqual({a:'5'})
  })

  it('Boolean直接覆盖',()=>{
    config.set({a:false})
    config.set({a:true})
    expect(config.get()).toEqual({a:true})
  })

})

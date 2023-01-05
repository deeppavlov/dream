import { getLanguage } from '../../src/utils'

describe('find the lang',()=>{

    it('end with lang',()=>{
        expect(getLanguage('<pre class="hljs language-jsx"><code>let abc</code></pre>')).toBe('jsx')
    })
    it('end with space',()=>{
        expect(getLanguage('<pre class="hljs language-jsx "><code>let abc</code></pre>')).toBe('jsx')
    })
    it('end with other class',()=>{
        expect(getLanguage('<pre class="hljs language-jsx font-small"><code>let abc</code></pre>')).toBe('jsx')
    })

    it('without highlight empty',()=>{
        expect(getLanguage('<pre class="hljs font-small"><code><span>let abc</span></code></pre>')).toBe('')
    })

    it('with highlight default',()=>{
        expect(getLanguage('<pre class="hljs font-small"><code><span class="hljs-keyword">let abc</span></code></pre>')).toBe('javascript')
    })

    it('with no lang',()=>{
        expect(getLanguage('<pre class="hljs language-"><code><span class="hljs-keyword">let abc</span></code></pre>')).toBe('')
    })
})

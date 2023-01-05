import html2Md from '../../src/index'
describe('some correction',()=>{

    it('Default no ignore svg',()=>{
        let str='<svg>\n' +
            '<path></path>\n' +
            ' </svg>'
        expect(html2Md(str)).toBe('')
    })

    it('Need to escape 1',()=>{
        let str='<p><strong>* 一个标题</strong></p>'
        expect(html2Md(str)).toBe('**\\* 一个标题**')
    })

    it('Need to escape 2',()=>{
        let str='<p><b>* 一个标题<i>- 第二个标题</i></b></p>'
        expect(html2Md(str)).toBe('**\\* 一个标题*\\- 第二个标题***')
    })
    it('Need to escape 3',()=>{
        let str='<p>**一个标题**<i>-- 第二个标题</i></p>'
        expect(html2Md(str)).toBe('\\*\\*一个标题\\*\\**\\-- 第二个标题*')
    })
    it('test starts with space',()=>{
        expect(html2Md(" <div><a>Sign In</a><a >Register</a></div>")).toBe("[Sign In]()[Register]()")
    })

    it('test no wrapper',()=>{
        expect(html2Md(" <b>bold</b><p>paragraph2</p>")).toBe("**bold**\n" +
            "\n" +
            "paragraph2")
    })
})

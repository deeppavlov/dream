import html2Md from '../../src/index'

describe('test codes',()=>{

  it('test-1',()=>{
    let str="<pre class=\"hljs\"><code><span class=\"hljs-comment\">/**\n * @param {number[]} stones\n * @return {number}\n */</span>\n<span class=\"hljs-keyword\">var</span> lastStoneWeight = <span class=\"hljs-function\"><span class=\"hljs-keyword\">function</span>(<span class=\"hljs-params\">stones</span>) </span>{\n  <span class=\"hljs-keyword\">let</span> pq=[]\n  <span class=\"hljs-function\"><span class=\"hljs-keyword\">function</span> <span class=\"hljs-title\">insert</span>(<span class=\"hljs-params\">n</span>)</span>{\n    <span class=\"hljs-keyword\">if</span>(pq.length===<span class=\"hljs-number\">0</span> || n&gt;=pq[pq.length<span class=\"hljs-number\">-1</span>]){\n      pq.push(n)\n    }<span class=\"hljs-keyword\">else</span>{\n      pq.splice(bsEnd(pq,n),<span class=\"hljs-number\">0</span>,n)\n    }\n  }\n  <span class=\"hljs-function\"><span class=\"hljs-keyword\">function</span> <span class=\"hljs-title\">bsEnd</span>(<span class=\"hljs-params\">arr,n</span>)</span>{\n    <span class=\"hljs-keyword\">let</span> lo=<span class=\"hljs-number\">0</span>,hi=arr.length<span class=\"hljs-number\">-1</span>\n    <span class=\"hljs-keyword\">while</span>(lo&lt;hi){\n      <span class=\"hljs-keyword\">let</span> mid=<span class=\"hljs-built_in\">Math</span>.floor((lo+hi)/<span class=\"hljs-number\">2</span>)\n      <span class=\"hljs-keyword\">if</span>(arr[mid]&lt;n)lo=mid+<span class=\"hljs-number\">1</span>\n      <span class=\"hljs-keyword\">else</span> hi=mid\n    }\n    <span class=\"hljs-keyword\">return</span> hi\n  }\n  <span class=\"hljs-function\"><span class=\"hljs-keyword\">function</span> <span class=\"hljs-title\">delMax</span>(<span class=\"hljs-params\"></span>)</span>{\n    <span class=\"hljs-keyword\">return</span> pq.pop()\n  }\n  <span class=\"hljs-keyword\">for</span>(<span class=\"hljs-keyword\">let</span> n <span class=\"hljs-keyword\">of</span> stones){\n    insert(n)\n  }\n  <span class=\"hljs-keyword\">while</span>(pq.length&gt;<span class=\"hljs-number\">1</span>){\n    <span class=\"hljs-keyword\">let</span> f=delMax(),\n        s=delMax()\n    <span class=\"hljs-keyword\">let</span> more=<span class=\"hljs-built_in\">Math</span>.max(f,s),\n        less=<span class=\"hljs-built_in\">Math</span>.min(f,s)\n    <span class=\"hljs-keyword\">if</span>(more===less)<span class=\"hljs-keyword\">continue</span>\n    more-=less\n    insert(more)\n  }\n  <span class=\"hljs-keyword\">if</span>(pq.length===<span class=\"hljs-number\">1</span>)<span class=\"hljs-keyword\">return</span> pq[<span class=\"hljs-number\">0</span>]\n  <span class=\"hljs-keyword\">return</span> <span class=\"hljs-number\">0</span>\n};\n</code></pre>\n"
    expect(html2Md(str)).toBe('```javascript\n' +
      '/**\n' +
      ' * @param {number[]} stones\n' +
      ' * @return {number}\n' +
      ' */\n' +
      'var lastStoneWeight = function(stones) {\n' +
      '  let pq=[]\n' +
      '  function insert(n){\n' +
      '    if(pq.length===0 || n>=pq[pq.length-1]){\n' +
      '      pq.push(n)\n' +
      '    }else{\n' +
      '      pq.splice(bsEnd(pq,n),0,n)\n' +
      '    }\n' +
      '  }\n' +
      '  function bsEnd(arr,n){\n' +
      '    let lo=0,hi=arr.length-1\n' +
      '    while(lo<hi){\n' +
      '      let mid=Math.floor((lo+hi)/2)\n' +
      '      if(arr[mid]<n)lo=mid+1\n' +
      '      else hi=mid\n' +
      '    }\n' +
      '    return hi\n' +
      '  }\n' +
      '  function delMax(){\n' +
      '    return pq.pop()\n' +
      '  }\n' +
      '  for(let n of stones){\n' +
      '    insert(n)\n' +
      '  }\n' +
      '  while(pq.length>1){\n' +
      '    let f=delMax(),\n' +
      '        s=delMax()\n' +
      '    let more=Math.max(f,s),\n' +
      '        less=Math.min(f,s)\n' +
      '    if(more===less)continue\n' +
      '    more-=less\n' +
      '    insert(more)\n' +
      '  }\n' +
      '  if(pq.length===1)return pq[0]\n' +
      '  return 0\n' +
      '};\n' +
      '```')
  })

  it('test-2',()=>{
    let str="<pre class=\"hljs\"><code><span class=\"hljs-comment\">/**\n * @param {number} N\n * @return {string}\n */</span>\n<span class=\"hljs-keyword\">var</span> baseNeg2 = <span class=\"hljs-function\"><span class=\"hljs-keyword\">function</span>(<span class=\"hljs-params\">N</span>) </span>{\n  <span class=\"hljs-keyword\">if</span>(N===<span class=\"hljs-number\">0</span>)<span class=\"hljs-keyword\">return</span> <span class=\"hljs-string\">'0'</span>\n  <span class=\"hljs-keyword\">let</span> aux=[]\n  <span class=\"hljs-keyword\">for</span>(<span class=\"hljs-keyword\">let</span> i=<span class=\"hljs-number\">0</span>;i&lt;=<span class=\"hljs-number\">32</span>;i++){\n    aux[i]=<span class=\"hljs-built_in\">Math</span>.pow(<span class=\"hljs-number\">-2</span>,i)\n  }\n  <span class=\"hljs-keyword\">let</span> sums=[aux[<span class=\"hljs-number\">0</span>],aux[<span class=\"hljs-number\">1</span>]]\n  <span class=\"hljs-keyword\">for</span>(<span class=\"hljs-keyword\">let</span> i=<span class=\"hljs-number\">2</span>;i&lt;aux.length;i+=<span class=\"hljs-number\">2</span>){\n    sums[i]=sums[i<span class=\"hljs-number\">-2</span>]+aux[i]\n  }\n  <span class=\"hljs-keyword\">for</span>(<span class=\"hljs-keyword\">let</span> i=<span class=\"hljs-number\">3</span>;i&lt;aux.length;i+=<span class=\"hljs-number\">2</span>){\n    sums[i]=sums[i<span class=\"hljs-number\">-2</span>]+aux[i]\n  }\n  <span class=\"hljs-keyword\">let</span> ans=<span class=\"hljs-literal\">null</span>\n  <span class=\"hljs-function\"><span class=\"hljs-keyword\">function</span> <span class=\"hljs-title\">calc</span>(<span class=\"hljs-params\">N,arr</span>)</span>{\n    <span class=\"hljs-keyword\">if</span>(ans)<span class=\"hljs-keyword\">return</span>\n    <span class=\"hljs-keyword\">let</span> delta=<span class=\"hljs-number\">2</span>,start=N&lt;<span class=\"hljs-number\">0</span> ? <span class=\"hljs-number\">1</span> : <span class=\"hljs-number\">0</span>\n    <span class=\"hljs-keyword\">for</span>(<span class=\"hljs-keyword\">let</span> i=start;i&lt;aux.length;i+=delta){\n      <span class=\"hljs-keyword\">if</span>(aux[i]===N){ \n        arr[i]=<span class=\"hljs-string\">'1'</span>\n        <span class=\"hljs-keyword\">return</span> ans=arr.slice()\n      }<span class=\"hljs-keyword\">else</span> <span class=\"hljs-keyword\">if</span>(<span class=\"hljs-built_in\">Math</span>.abs(sums[i])&gt;=<span class=\"hljs-built_in\">Math</span>.abs(N)){\n        arr[i]=<span class=\"hljs-string\">'1'</span>\n        calc(N-aux[i],arr)\n        <span class=\"hljs-keyword\">if</span>(ans)<span class=\"hljs-keyword\">return</span>\n      }\n    }\n  }\n  calc(N,[])\n  <span class=\"hljs-keyword\">let</span> finalAns=<span class=\"hljs-string\">''</span>\n  <span class=\"hljs-keyword\">for</span>(<span class=\"hljs-keyword\">let</span> i=ans.length<span class=\"hljs-number\">-1</span>;i&gt;=<span class=\"hljs-number\">0</span>;i--){\n    <span class=\"hljs-keyword\">if</span>(ans[i]==<span class=\"hljs-literal\">null</span>)finalAns+=<span class=\"hljs-string\">'0'</span>\n    <span class=\"hljs-keyword\">else</span> finalAns+=ans[i]\n  }\n  <span class=\"hljs-keyword\">return</span> finalAns\n};\n</code></pre>\n"
    expect(html2Md(str)).toBe('```javascript\n' +
      '/**\n' +
      ' * @param {number} N\n' +
      ' * @return {string}\n' +
      ' */\n' +
      'var baseNeg2 = function(N) {\n' +
      '  if(N===0)return \'0\'\n' +
      '  let aux=[]\n' +
      '  for(let i=0;i<=32;i++){\n' +
      '    aux[i]=Math.pow(-2,i)\n' +
      '  }\n' +
      '  let sums=[aux[0],aux[1]]\n' +
      '  for(let i=2;i<aux.length;i+=2){\n' +
      '    sums[i]=sums[i-2]+aux[i]\n' +
      '  }\n' +
      '  for(let i=3;i<aux.length;i+=2){\n' +
      '    sums[i]=sums[i-2]+aux[i]\n' +
      '  }\n' +
      '  let ans=null\n' +
      '  function calc(N,arr){\n' +
      '    if(ans)return\n' +
      '    let delta=2,start=N<0 ? 1 : 0\n' +
      '    for(let i=start;i<aux.length;i+=delta){\n' +
      '      if(aux[i]===N){ \n' +
      '        arr[i]=\'1\'\n' +
      '        return ans=arr.slice()\n' +
      '      }else if(Math.abs(sums[i])>=Math.abs(N)){\n' +
      '        arr[i]=\'1\'\n' +
      '        calc(N-aux[i],arr)\n' +
      '        if(ans)return\n' +
      '      }\n' +
      '    }\n' +
      '  }\n' +
      '  calc(N,[])\n' +
      '  let finalAns=\'\'\n' +
      '  for(let i=ans.length-1;i>=0;i--){\n' +
      '    if(ans[i]==null)finalAns+=\'0\'\n' +
      '    else finalAns+=ans[i]\n' +
      '  }\n' +
      '  return finalAns\n' +
      '};\n' +
      '```')
  })

})

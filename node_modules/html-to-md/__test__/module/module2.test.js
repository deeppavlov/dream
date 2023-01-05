import html2Md from '../../src/index'

describe('test modules',()=>{

  it('test-1',()=>{
    let str="<p>在&nbsp;<code>N x N</code>&nbsp;的网格上，每个单元格&nbsp;<code>(x, y)</code>&nbsp;上都有一盏灯，其中&nbsp;<code>0 &lt;= x &lt; N</code>&nbsp;且&nbsp;<code>0 &lt;= y &lt; N</code> 。</p>\n\n<p>最初，一定数量的灯是亮着的。<code>lamps[i]</code>&nbsp;告诉我们亮着的第 <code>i</code> 盏灯的位置。每盏灯都照亮其所在 x 轴、y 轴和两条对角线上的每个正方形（类似于国际象棋中的皇后）。</p>\n\n<p>对于第 <code>i</code> 次查询&nbsp;<code>queries[i] = (x, y)</code>，如果单元格 (x, y) 是被照亮的，则查询结果为 1，否则为 0 。</p>\n\n<p>在每个查询 <code>(x, y)</code> 之后 [按照查询的顺序]，我们关闭位于单元格 (x, y) 上或其相邻 8 个方向上（与单元格 (x, y) 共享一个角或边）的任何灯。</p>\n\n<p>返回答案数组 <code>answer</code>。每个值 <code>answer[i]</code> 应等于第 <code>i</code>&nbsp;次查询&nbsp;<code>queries[i]</code>&nbsp;的结果。</p>\n\n<p>&nbsp;</p>\n\n<p><strong>示例：</strong></p>\n\n<pre><strong>输入：</strong>N = 5, lamps = [[0,0],[4,4]], queries = [[1,1],[1,0]]\n<strong>输出：</strong>[1,0]\n<strong>解释： </strong>\n在执行第一次查询之前，我们位于 [0, 0] 和 [4, 4] 灯是亮着的。\n表示哪些单元格亮起的网格如下所示，其中 [0, 0] 位于左上角：\n1 1 1 1 1\n1 1 0 0 1\n1 0 1 0 1\n1 0 0 1 1\n1 1 1 1 1\n然后，由于单元格 [1, 1] 亮着，第一次查询返回 1。在此查询后，位于 [0，0] 处的灯将关闭，网格现在如下所示：\n1 0 0 0 1\n0 1 0 0 1\n0 0 1 0 1\n0 0 0 1 1\n1 1 1 1 1\n在执行第二次查询之前，我们只有 [4, 4] 处的灯亮着。现在，[1, 0] 处的查询返回 0，因为该单元格不再亮着。\n</pre>\n\n<p>&nbsp;</p>\n\n<p><strong>提示：</strong></p>\n\n<ol>\n\t<li><code>1 &lt;= N &lt;= 10^9</code></li>\n\t<li><code>0 &lt;= lamps.length &lt;= 20000</code></li>\n\t<li><code>0 &lt;= queries.length &lt;= 20000</code></li>\n\t<li><code>lamps[i].length == queries[i].length == 2</code></li>\n</ol>\n"
    expect(html2Md(str)).toBe('在 `N x N` 的网格上，每个单元格 `(x, y)` 上都有一盏灯，其中 `0 <= x < N` 且 `0 <= y < N` 。\n' +
      '\n' +
      '最初，一定数量的灯是亮着的。`lamps[i]` 告诉我们亮着的第 `i` 盏灯的位置。每盏灯都照亮其所在 x 轴、y 轴和两条对角线上的每个正方形（类似于国际象棋中的皇后）。\n' +
      '\n' +
      '对于第 `i` 次查询 `queries[i] = (x, y)`，如果单元格 (x, y) 是被照亮的，则查询结果为 1，否则为 0 。\n' +
      '\n' +
      '在每个查询 `(x, y)` 之后 \\[按照查询的顺序\\]，我们关闭位于单元格 (x, y) 上或其相邻 8 个方向上（与单元格 (x, y) 共享一个角或边）的任何灯。\n' +
      '\n' +
      '返回答案数组 `answer`。每个值 `answer[i]` 应等于第 `i` 次查询 `queries[i]` 的结果。\n' +
      '\n' +
      '**示例：**\n' +
      '\n' +
      '```\n' +
      '输入：N = 5, lamps = [[0,0],[4,4]], queries = [[1,1],[1,0]]\n' +
      '输出：[1,0]\n' +
      '解释： \n' +
      '在执行第一次查询之前，我们位于 [0, 0] 和 [4, 4] 灯是亮着的。\n' +
      '表示哪些单元格亮起的网格如下所示，其中 [0, 0] 位于左上角：\n' +
      '1 1 1 1 1\n' +
      '1 1 0 0 1\n' +
      '1 0 1 0 1\n' +
      '1 0 0 1 1\n' +
      '1 1 1 1 1\n' +
      '然后，由于单元格 [1, 1] 亮着，第一次查询返回 1。在此查询后，位于 [0，0] 处的灯将关闭，网格现在如下所示：\n' +
      '1 0 0 0 1\n' +
      '0 1 0 0 1\n' +
      '0 0 1 0 1\n' +
      '0 0 0 1 1\n' +
      '1 1 1 1 1\n' +
      '在执行第二次查询之前，我们只有 [4, 4] 处的灯亮着。现在，[1, 0] 处的查询返回 0，因为该单元格不再亮着。\n' +
      '```\n' +
      '\n' +
      '**提示：**\n' +
      '\n' +
      '1. `1 <= N <= 10^9`\n' +
      '2. `0 <= lamps.length <= 20000`\n' +
      '3. `0 <= queries.length <= 20000`\n' +
      '4. `lamps[i].length == queries[i].length == 2`')
  })

  it('test-2',()=>{
    let str="<p>给出一个二维数组&nbsp;<code>A</code>，每个单元格为 0（代表海）或 1（代表陆地）。</p>\n\n<p>移动是指在陆地上从一个地方走到另一个地方（朝四个方向之一）或离开网格的边界。</p>\n\n<p>返回网格中<strong>无法</strong>在任意次数的移动中离开网格边界的陆地单元格的数量。</p>\n\n<p>&nbsp;</p>\n\n<p><strong>示例 1：</strong></p>\n\n<pre><strong>输入：</strong>[[0,0,0,0],[1,0,1,0],[0,1,1,0],[0,0,0,0]]\n<strong>输出：</strong>3\n<strong>解释： </strong>\n有三个 1 被 0 包围。一个 1 没有被包围，因为它在边界上。</pre>\n\n<p><strong>示例 2：</strong></p>\n\n<pre><strong>输入：</strong>[[0,1,1,0],[0,0,1,0],[0,0,1,0],[0,0,0,0]]\n<strong>输出：</strong>0\n<strong>解释：</strong>\n所有 1 都在边界上或可以到达边界。</pre>\n\n<p>&nbsp;</p>\n\n<p><strong>提示：</strong></p>\n\n<ol>\n\t<li><code>1 &lt;= A.length &lt;= 500</code></li>\n\t<li><code>1 &lt;= A[i].length &lt;= 500</code></li>\n\t<li><code>0 &lt;= A[i][j] &lt;= 1</code></li>\n\t<li>所有行的大小都相同</li>\n</ol>\n"
    expect(html2Md(str)).toBe('给出一个二维数组 `A`，每个单元格为 0（代表海）或 1（代表陆地）。\n' +
      '\n' +
      '移动是指在陆地上从一个地方走到另一个地方（朝四个方向之一）或离开网格的边界。\n' +
      '\n' +
      '返回网格中**无法**在任意次数的移动中离开网格边界的陆地单元格的数量。\n' +
      '\n' +
      '**示例 1：**\n' +
      '\n' +
      '```\n' +
      '输入：[[0,0,0,0],[1,0,1,0],[0,1,1,0],[0,0,0,0]]\n' +
      '输出：3\n' +
      '解释： \n' +
      '有三个 1 被 0 包围。一个 1 没有被包围，因为它在边界上。\n' +
      '```\n' +
      '\n' +
      '**示例 2：**\n' +
      '\n' +
      '```\n' +
      '输入：[[0,1,1,0],[0,0,1,0],[0,0,1,0],[0,0,0,0]]\n' +
      '输出：0\n' +
      '解释：\n' +
      '所有 1 都在边界上或可以到达边界。\n' +
      '```\n' +
      '\n' +
      '**提示：**\n' +
      '\n' +
      '1. `1 <= A.length <= 500`\n' +
      '2. `1 <= A[i].length <= 500`\n' +
      '3. `0 <= A[i][j] <= 1`\n' +
      '4. 所有行的大小都相同')
  })

  it('test-3',()=>{
    let str="<style>\r\ntable.dungeon, .dungeon th, .dungeon td {\r\n  border:3px solid black;\r\n}\r\n\r\n .dungeon th, .dungeon td {\r\n    text-align: center;\r\n    height: 70px;\r\n    width: 70px;\r\n}\r\n</style>\r\n\r\n<p>一些恶魔抓住了公主（<strong>P</strong>）并将她关在了地下城的右下角。地下城是由&nbsp;M x N 个房间组成的二维网格。我们英勇的骑士（<strong>K</strong>）最初被安置在左上角的房间里，他必须穿过地下城并通过对抗恶魔来拯救公主。</p>\r\n\r\n<p>骑士的初始健康点数为一个正整数。如果他的健康点数在某一时刻降至 0 或以下，他会立即死亡。</p>\r\n\r\n<p>有些房间由恶魔守卫，<!---2K   -3  3\n-5   -10   1\n10 30   5P-->因此骑士在进入这些房间时会失去健康点数（若房间里的值为<em>负整数</em>，则表示骑士将损失健康点数）；其他房间要么是空的（房间里的值为 <em>0</em>），要么包含增加骑士健康点数的魔法球（若房间里的值为<em>正整数</em>，则表示骑士将增加健康点数）。</p>\r\n\r\n<p>为了尽快到达公主，骑士决定每次只向右或向下移动一步。</p>\r\n\r\n<p>&nbsp;</p>\r\n\r\n<p><strong>编写一个函数来计算确保骑士能够拯救到公主所需的最低初始健康点数。</strong></p>\r\n\r\n<p>例如，考虑到如下布局的地下城，如果骑士遵循最佳路径 <code>右 -&gt; 右 -&gt; 下 -&gt; 下</code>，则骑士的初始健康点数至少为 <strong>7</strong>。</p>\r\n\r\n<table class=\"dungeon\">\r\n<tr> \r\n<td>-2 (K)</td> \r\n<td>-3</td> \r\n<td>3</td> \r\n</tr> \r\n<tr> \r\n<td>-5</td> \r\n<td>-10</td> \r\n<td>1</td> \r\n</tr> \r\n<tr> \r\n<td>10</td> \r\n<td>30</td> \r\n<td>-5 (P)</td> \r\n</tr> \r\n</table>\r\n<!---2K   -3  3\r\n-5   -10   1\r\n10 30   5P-->\r\n\r\n<p>&nbsp;</p>\r\n\r\n<p><strong>说明:</strong></p>\r\n\r\n<ul>\r\n\t<li>\r\n\t<p>骑士的健康点数没有上限。</p>\r\n\t</li>\r\n\t<li>任何房间都可能对骑士的健康点数造成威胁，也可能增加骑士的健康点数，包括骑士进入的左上角房间以及公主被监禁的右下角房间。</li>\r\n</ul>"
    expect(html2Md(str)).toBe('一些恶魔抓住了公主（**P**）并将她关在了地下城的右下角。地下城是由 M x N 个房间组成的二维网格。我们英勇的骑士（**K**）最初被安置在左上角的房间里，他必须穿过地下城并通过对抗恶魔来拯救公主。\n' +
      '\n' +
      '骑士的初始健康点数为一个正整数。如果他的健康点数在某一时刻降至 0 或以下，他会立即死亡。\n' +
      '\n' +
      '有些房间由恶魔守卫，因此骑士在进入这些房间时会失去健康点数（若房间里的值为*负整数*，则表示骑士将损失健康点数）；其他房间要么是空的（房间里的值为 *0*），要么包含增加骑士健康点数的魔法球（若房间里的值为*正整数*，则表示骑士将增加健康点数）。\n' +
      '\n' +
      '为了尽快到达公主，骑士决定每次只向右或向下移动一步。\n' +
      '\n' +
      '**编写一个函数来计算确保骑士能够拯救到公主所需的最低初始健康点数。**\n' +
      '\n' +
      '例如，考虑到如下布局的地下城，如果骑士遵循最佳路径 `右 -> 右 -> 下 -> 下`，则骑士的初始健康点数至少为 **7**。\n' +
      '\n' +
      '||||\n' +
      '|---|---|---|\n' +
      '|\\-2 (K)|\\-3|3|\n' +
      '|\\-5|\\-10|1|\n' +
      '|10|30|\\-5 (P)|\n' +
      '\n' +
      '**说明:**\n' +
      '\n' +
      '* 骑士的健康点数没有上限。\n' +
      '* 任何房间都可能对骑士的健康点数造成威胁，也可能增加骑士的健康点数，包括骑士进入的左上角房间以及公主被监禁的右下角房间。')
  })

  it('test-4',()=>{
    let str="<p>班上有&nbsp;<strong>N&nbsp;</strong>名学生。其中有些人是朋友，有些则不是。他们的友谊具有是传递性。如果已知 A 是 B&nbsp;的朋友，B 是 C&nbsp;的朋友，那么我们可以认为 A 也是 C&nbsp;的朋友。所谓的朋友圈，是指所有朋友的集合。</p>\n\n<p>给定一个&nbsp;<strong>N * N&nbsp;</strong>的矩阵&nbsp;<strong>M</strong>，表示班级中学生之间的朋友关系。如果M[i][j] = 1，表示已知第 i 个和 j 个学生<strong>互为</strong>朋友关系，否则为不知道。你必须输出所有学生中的已知的朋友圈总数。</p>\n\n<p><strong>示例 1:</strong></p>\n\n<pre>\n<strong>输入:</strong> \n[[1,1,0],\n [1,1,0],\n [0,0,1]]\n<strong>输出:</strong> 2 \n<strong>说明：</strong>已知学生0和学生1互为朋友，他们在一个朋友圈。\n第2个学生自己在一个朋友圈。所以返回2。\n</pre>\n\n<p><strong>示例 2:</strong></p>\n\n<pre>\n<strong>输入:</strong> \n[[1,1,0],\n [1,1,1],\n [0,1,1]]\n<strong>输出:</strong> 1\n<strong>说明：</strong>已知学生0和学生1互为朋友，学生1和学生2互为朋友，所以学生0和学生2也是朋友，所以他们三个在一个朋友圈，返回1。\n</pre>\n\n<p><strong>注意：</strong></p>\n\n<ol>\n\t<li>N 在[1,200]的范围内。</li>\n\t<li>对于所有学生，有M[i][i] = 1。</li>\n\t<li>如果有M[i][j] = 1，则有M[j][i] = 1。</li>\n</ol>\n"
    expect(html2Md(str)).toBe(`班上有 **N**名学生。其中有些人是朋友，有些则不是。他们的友谊具有是传递性。如果已知 A 是 B 的朋友，B 是 C 的朋友，那么我们可以认为 A 也是 C 的朋友。所谓的朋友圈，是指所有朋友的集合。

给定一个 **N \\* N**的矩阵 **M**，表示班级中学生之间的朋友关系。如果M\\[i\\]\\[j\\] = 1，表示已知第 i 个和 j 个学生**互为**朋友关系，否则为不知道。你必须输出所有学生中的已知的朋友圈总数。

**示例 1:**

\`\`\`

输入: 
[[1,1,0],
 [1,1,0],
 [0,0,1]]
输出: 2 
说明：已知学生0和学生1互为朋友，他们在一个朋友圈。
第2个学生自己在一个朋友圈。所以返回2。
\`\`\`

**示例 2:**

\`\`\`

输入: 
[[1,1,0],
 [1,1,1],
 [0,1,1]]
输出: 1
说明：已知学生0和学生1互为朋友，学生1和学生2互为朋友，所以学生0和学生2也是朋友，所以他们三个在一个朋友圈，返回1。
\`\`\`

**注意：**

1. N 在\\[1,200\\]的范围内。
2. 对于所有学生，有M\\[i\\]\\[i\\] = 1。
3. 如果有M\\[i\\]\\[j\\] = 1，则有M\\[j\\]\\[i\\] = 1。`)
  })

  it('test-5',()=>{
    let str="<p>有一堆石头，每块石头的重量都是正整数。</p>\n\n<p>每一回合，从中选出两块<strong>最重的</strong>石头，然后将它们一起粉碎。假设石头的重量分别为&nbsp;<code>x</code> 和&nbsp;<code>y</code>，且&nbsp;<code>x &lt;= y</code>。那么粉碎的可能结果如下：</p>\n\n<ul>\n\t<li>如果&nbsp;<code>x == y</code>，那么两块石头都会被完全粉碎；</li>\n\t<li>如果&nbsp;<code>x != y</code>，那么重量为&nbsp;<code>x</code>&nbsp;的石头将会完全粉碎，而重量为&nbsp;<code>y</code>&nbsp;的石头新重量为&nbsp;<code>y-x</code>。</li>\n</ul>\n\n<p>最后，最多只会剩下一块石头。返回此石头的重量。如果没有石头剩下，就返回 <code>0</code>。</p>\n\n<p>&nbsp;</p>\n\n<p><strong>提示：</strong></p>\n\n<ol>\n\t<li><code>1 &lt;= stones.length &lt;= 30</code></li>\n\t<li><code>1 &lt;= stones[i] &lt;= 1000</code></li>\n</ol>\n"
    expect(html2Md(str)).toBe('有一堆石头，每块石头的重量都是正整数。\n' +
      '\n' +
      '每一回合，从中选出两块**最重的**石头，然后将它们一起粉碎。假设石头的重量分别为 `x` 和 `y`，且 `x <= y`。那么粉碎的可能结果如下：\n' +
      '\n' +
      '* 如果 `x == y`，那么两块石头都会被完全粉碎；\n' +
      '* 如果 `x != y`，那么重量为 `x` 的石头将会完全粉碎，而重量为 `y` 的石头新重量为 `y-x`。\n' +
      '\n' +
      '最后，最多只会剩下一块石头。返回此石头的重量。如果没有石头剩下，就返回 `0`。\n' +
      '\n' +
      '**提示：**\n' +
      '\n' +
      '1. `1 <= stones.length <= 30`\n' +
      '2. `1 <= stones[i] <= 1000`')
  })

  it('test-6',()=>{
    let str="<p>返回与给定先序遍历&nbsp;<code>preorder</code> 相匹配的二叉搜索树（binary <strong>search</strong> tree）的根结点。</p>\n\n<p><em>(回想一下，二叉搜索树是二叉树的一种，其每个节点都满足以下规则，对于&nbsp;<code>node.left</code>&nbsp;的任何后代，值总 <code>&lt;</code> <code>node.val</code>，而 <code>node.right</code> 的任何后代，值总 <code>&gt;</code> <code>node.val</code>。此外，先序遍历首先显示节点的值，然后遍历 <code>node.left</code>，接着遍历 <code>node.right</code>。）</em></p>\n\n<p>&nbsp;</p>\n\n<p><strong>示例：</strong></p>\n\n<pre><strong>输入：</strong>[8,5,1,7,10,12]\n<strong>输出：</strong>[8,5,10,1,7,null,12]\n<img alt=\"\" src=\"https://assets.leetcode-cn.com/aliyun-lc-upload/uploads/2019/03/08/1266.png\" style=\"height: 200px; width: 306px;\">\n</pre>\n\n<p>&nbsp;</p>\n\n<p><strong>提示：</strong></p>\n\n<ol>\n\t<li><code>1 &lt;= preorder.length &lt;= 100</code></li>\n\t<li>先序&nbsp;<code>preorder</code>&nbsp;中的值是不同的。</li>\n</ol>\n"
    expect(html2Md(str)).toBe(`返回与给定先序遍历 \`preorder\` 相匹配的二叉搜索树（binary **search** tree）的根结点。

*(回想一下，二叉搜索树是二叉树的一种，其每个节点都满足以下规则，对于 \`node.left\` 的任何后代，值总 \`<\` \`node.val\`，而 \`node.right\` 的任何后代，值总 \`>\` \`node.val\`。此外，先序遍历首先显示节点的值，然后遍历 \`node.left\`，接着遍历 \`node.right\`。）*

**示例：**

\`\`\`
输入：[8,5,1,7,10,12]
输出：[8,5,10,1,7,null,12]

\`\`\`

**提示：**

1. \`1 <= preorder.length <= 100\`
2. 先序 \`preorder\` 中的值是不同的。`)
  })

  it('test-7',()=>{
    let str="<p>给定一个由空格分割单词的句子&nbsp;<code>S</code>。每个单词只包含大写或小写字母。</p>\n\n<p>我们要将句子转换为&nbsp;<em>&ldquo;Goat Latin&rdquo;</em>（一种类似于 猪拉丁文&nbsp;- Pig Latin 的虚构语言）。</p>\n\n<p>山羊拉丁文的规则如下：</p>\n\n<ul>\n\t<li>如果单词以元音开头（a, e, i, o, u），在单词后添加<code>&quot;ma&quot;</code>。<br />\n\t例如，单词<code>&quot;apple&quot;</code>变为<code>&quot;applema&quot;</code>。</li>\n\t<br />\n\t<li>如果单词以辅音字母开头（即非元音字母），移除第一个字符并将它放到末尾，之后再添加<code>&quot;ma&quot;</code>。<br />\n\t例如，单词<code>&quot;goat&quot;</code>变为<code>&quot;oatgma&quot;</code>。</li>\n\t<br />\n\t<li>根据单词在句子中的索引，在单词最后添加与索引相同数量的字母<code>&#39;a&#39;</code>，索引从1开始。<br />\n\t例如，在第一个单词后添加<code>&quot;a&quot;</code>，在第二个单词后添加<code>&quot;aa&quot;</code>，以此类推。</li>\n</ul>\n\n<p>返回将&nbsp;<code>S</code>&nbsp;转换为山羊拉丁文后的句子。</p>\n\n<p><strong>示例 1:</strong></p>\n\n<pre>\n<strong>输入: </strong>&quot;I speak Goat Latin&quot;\n<strong>输出: </strong>&quot;Imaa peaksmaaa oatGmaaaa atinLmaaaaa&quot;\n</pre>\n\n<p><strong>示例 2:</strong></p>\n\n<pre>\n<strong>输入: </strong>&quot;The quick brown fox jumped over the lazy dog&quot;\n<strong>输出: </strong>&quot;heTmaa uickqmaaa rownbmaaaa oxfmaaaaa umpedjmaaaaaa overmaaaaaaa hetmaaaaaaaa azylmaaaaaaaaa ogdmaaaaaaaaaa&quot;\n</pre>\n\n<p><strong>说明:</strong></p>\n\n<ul>\n\t<li><code>S</code>&nbsp;中仅包含大小写字母和空格。单词间有且仅有一个空格。</li>\n\t<li><code>1 &lt;= S.length &lt;= 150</code>。</li>\n</ul>\n"
    expect(html2Md(str)).toBe(`给定一个由空格分割单词的句子 \`S\`。每个单词只包含大写或小写字母。

我们要将句子转换为 *“Goat Latin”*（一种类似于 猪拉丁文 - Pig Latin 的虚构语言）。

山羊拉丁文的规则如下：

* 如果单词以元音开头（a, e, i, o, u），在单词后添加\`"ma"\`。  
  例如，单词\`"apple"\`变为\`"applema"\`。
* 如果单词以辅音字母开头（即非元音字母），移除第一个字符并将它放到末尾，之后再添加\`"ma"\`。  
  例如，单词\`"goat"\`变为\`"oatgma"\`。
* 根据单词在句子中的索引，在单词最后添加与索引相同数量的字母\`'a'\`，索引从1开始。  
  例如，在第一个单词后添加\`"a"\`，在第二个单词后添加\`"aa"\`，以此类推。

返回将 \`S\` 转换为山羊拉丁文后的句子。

**示例 1:**

\`\`\`

输入: "I speak Goat Latin"
输出: "Imaa peaksmaaa oatGmaaaa atinLmaaaaa"
\`\`\`

**示例 2:**

\`\`\`

输入: "The quick brown fox jumped over the lazy dog"
输出: "heTmaa uickqmaaa rownbmaaaa oxfmaaaaa umpedjmaaaaaa overmaaaaaaa hetmaaaaaaaa azylmaaaaaaaaa ogdmaaaaaaaaaa"
\`\`\`

**说明:**

* \`S\` 中仅包含大小写字母和空格。单词间有且仅有一个空格。
* \`1 <= S.length <= 150\`。`)
  })

})

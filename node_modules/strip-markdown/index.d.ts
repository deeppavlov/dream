/**
 * Plugin to remove markdown formatting.
 *
 * @type {import('unified').Plugin<[Options?] | void[], Root>}
 */
export default function stripMarkdown(
  options?: void | Options | undefined
):
  | void
  | import('unified').Transformer<import('mdast').Root, import('mdast').Root>
export type Content = import('mdast').Content
export type Root = import('mdast').Root
export type Node = Root | Content
export type Type = Node['type']
export type Handler = (node: any) => Node | Node[]
export type Handlers = Partial<Record<Type, Handler>>
/**
 * Configuration.
 */
export type Options = {
  /**
   * List of node types to leave unchanged.
   */
  keep?: Array<Type> | undefined
  /**
   * List of additional node types to remove or replace.
   */
  remove?: Array<Type | [Type, Handler]> | undefined
}

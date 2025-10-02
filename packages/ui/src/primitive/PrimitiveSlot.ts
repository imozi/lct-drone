import { cloneVNode, Comment, Fragment, defineComponent, mergeProps, type VNode } from 'vue';

function renderSlotFragments(children?: VNode[]): VNode[] {
  if (!children) return [];
  return children.flatMap((child) => (child.type === Fragment ? renderSlotFragments(child.children as VNode[]) : [child]));
}

export const PrimitiveSlot = defineComponent({
  name: 'PrimitiveSlot',
  inheritAttrs: false,
  setup(_, { attrs, slots }) {
    return () => {
      if (!slots.default) return null;

      const children = renderSlotFragments(slots.default());

      if (children.length === 0) return null;

      const nonCommentChildIndex = children.findIndex((child) => child.type !== Comment);

      if (nonCommentChildIndex === -1) return null;

      const nonCommentChild = children[nonCommentChildIndex];

      if (nonCommentChild.props?.ref) {
        delete nonCommentChild.props.ref;
      }

      const mergedProps = nonCommentChild.props ? mergeProps(attrs, nonCommentChild.props) : attrs;
      const cloned = cloneVNode({ ...nonCommentChild, props: {} }, mergedProps);

      if (children.length === 1) {
        return cloned;
      } else {
        children[nonCommentChildIndex] = cloned;
        return children;
      }
    };
  },
});

<template>
    <div class="tw-overflow-visible tw-relative bg-opacity-100" :class="offset_classes">
      <optional-router-link :to="'/user/'+user.username" :disabled="!linktoprofile">
        <UserAvatar
          :size="size"
          :user="user"
          :tooltip="tooltip"
        >
        </UserAvatar>
      </optional-router-link>
    </div>
</template>

<script lang="ts">
import OptionalRouterLink from 'components/global/OptionalRouterLink.vue';
import UserAvatar from 'components/global/UserAvatar.vue';
import { SizeType, isValidSizeType } from 'src/constants';
import { User } from 'src/models/experiment';
import { PropType } from 'vue';

export default {
  name: 'ProfileImage',
  components: {UserAvatar, OptionalRouterLink},

  props: {
    offset_classes: {
      type: String,
      default: ''
    },
    user: {
      type: Object as PropType<User>,
      required: true
    },
    size: {
      type: String as () => SizeType,
      default: 'md',
      validators: [isValidSizeType]
    },
    tooltip: {
      type: Boolean,
      default: false
    },
    linktoprofile: {
      type: Boolean,
      default: false
    },
    avatar: {
      type: String,
      default: ''
    }
  },
}
</script>

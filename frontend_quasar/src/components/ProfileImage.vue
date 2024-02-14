<template>
    <div class="tw-overflow-visible tw-relative bg-opacity-100" :class="offset_classes">
      <optional-router-link :to="'/user/'+username" :disabled="!linktoprofile">
        <UserAvatar
          :size="size"
          :img="avatar"
          :username="username"
          :tooltip="tooltip"
        >
        </UserAvatar>
      </optional-router-link>
    </div>
</template>

<script lang="ts">
import OptionalRouterLink from 'components/global/OptionalRouterLink.vue';
import UserAvatar from 'components/global/UserAvatar.vue';


export default {
  name: 'ProfileImage',
  components: {UserAvatar, OptionalRouterLink},

  props: {
    offset_classes: {
      type: String,
      default: ''
    },
    username: {
      type: String,
      default: ''
    },
    size: {
      type: String,
      default: 'md'
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

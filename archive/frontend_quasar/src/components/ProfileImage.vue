<template>
    <div class="tw-overflow-visible tw-relative bg-opacity-100" :class="offsetClasses" v-if="profile">

      <a :href="'/user/'+profile.user.username" :class="{ 'disabled-link': !linkToProfile }">
        <UserAvatar
          :size="size"
          :profile="profile"
          :tooltip="tooltip"
        >
        </UserAvatar>
      </a>

    </div>
</template>

<script lang="ts">
import UserAvatar from 'components/global/UserAvatar.vue';
import { SizeType, isValidSizeType } from 'src/constants';
import { Profile } from 'src/models/experiment';
import { PropType } from 'vue';

export default {
  name: 'ProfileImage',
  components: {UserAvatar},

  props: {
    offsetClasses: {
      type: String,
      default: ''
    },
    profile: {
      type: Object as PropType<Profile>,
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
    linkToProfile: {
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

<style scoped>
.disabled-link {
  pointer-events: none;
  cursor: default;
}
</style>

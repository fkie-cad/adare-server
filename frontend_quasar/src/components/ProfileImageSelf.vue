<template>
    <div class="tw-overflow-visible tw-relative" :class="offset_classes">
      <UserAvatar
        :size="size"
        :img="LoggedInUserStore.avatar"
        :username="LoggedInUserStore.username"
      />
    </div>
</template>

<script lang="ts">
import { useUserStore } from 'src/store/user';
import { useLoggedInUserStore } from 'src/store/loggedinuser';
import {ref} from 'vue';
import { storeToRefs } from 'pinia';
import UserAvatar from 'components/global/UserAvatar.vue';
import { isValidSizeType, SizeType } from 'src/constants';


export default {
  name: 'ProfileImageSelf',
  components: {UserAvatar},

  props: {
    editable: {
      type: Boolean,
      default: false
    },
    offset_classes: {
      type: String,
      default: ''
    },
    username: {
      type: String,
      default: ''
    },
    size: {
      type: String as () => SizeType,
      default: 'md',
      validators: [isValidSizeType]
    },
  },

  setup() {

    const show_dialog = ref(false)
    const LoggedInUserStore = useLoggedInUserStore()
    storeToRefs(LoggedInUserStore)
    const UserStore = useUserStore()
    storeToRefs(UserStore)
    const file = ref<File | null>(null)

    return {
      LoggedInUserStore,
      file,
      show_dialog,
    }

  }
}
</script>

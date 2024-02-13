<template>
    <div class="tw-overflow-visible tw-relative bg-opacity-100" :class="offset_classes">
      <optional-router-link :to="'/user/'+username" :disabled="!linktoprofile">
        <UserAvatar
          :size="size"
          :img="UserStore.GetUserAvatarThumbnail(username)"
          :username="username"
        >
          <q-tooltip v-if="tooltip">
            {{ username }}
          </q-tooltip>
        </UserAvatar>
      </optional-router-link>
    </div>
</template>

<script lang="ts">
import { useUserStore } from 'stores/user';
import { useLoggedInUserStore } from 'stores/loggedinuser';
import { storeToRefs } from 'pinia'
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
    avatar_url: {
      type: String,
      default: ''
    }
  },

  setup(props) {


    const LoggedInUserStore = useLoggedInUserStore()
    storeToRefs(LoggedInUserStore)

    const UserStore = useUserStore()
    storeToRefs(UserStore)

    return {
      UserStore,
    }

  }
}
</script>

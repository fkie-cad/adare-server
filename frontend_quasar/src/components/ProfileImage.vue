<template>
    <div class="tw-overflow-visible tw-relative bg-opacity-100" :class="offset_classes">
      <optional-router-link :to="'/user/'+username" :disabled="!linktoprofile">
      <q-avatar
        color="secondary"
        :size="size_to_width[size]"
        text-color="white"
      >
        <q-tooltip v-if="tooltip">
          {{ username }}
        </q-tooltip>
        <div v-if=" UserStore.GetUserAvatarThumbnail(username, size) != ''">
            <img v-bind:src=" UserStore.GetUserAvatarThumbnail(username, size)" alt="" class="object-cover">
        </div>
        <div v-else>
          {{ username.charAt(0).toUpperCase() }}
        </div>
      </q-avatar>
      </optional-router-link>
    </div>
</template>

<script lang="ts">
import { useUserStore } from 'stores/user';
import { useLoggedInUserStore } from 'stores/loggedinuser';
import {onMounted, ref} from 'vue';
import { storeToRefs } from 'pinia'
import OptionalRouterLink from 'components/global/OptionalRouterLink.vue';


export default {
  name: 'ProfileImage',
  components: {OptionalRouterLink},

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
  },

  setup(props) {

    const size_to_width = {
      'sm': '30px',
      'md': '50px',
      'lg': '100px',
    }

    const LoggedInUserStore = useLoggedInUserStore()
    storeToRefs(LoggedInUserStore)
    const UserStore = useUserStore()
    storeToRefs(UserStore)
    const file = ref<File | null>(null)


    onMounted(async () => {
      await UserStore.UpdateProfileInformation(props.username)
    })

    return {
      UserStore,
      size_to_width,
      file,
    }

  }
}
</script>

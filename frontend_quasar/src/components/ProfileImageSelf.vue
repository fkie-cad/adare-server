<template>
    <div class="tw-overflow-visible tw-relative" :class="offset_classes">
      <UserAvatar
        :size="size"
        :img="LoggedInUserStore.GetUserAvatarThumbnail(size)"
        :username="LoggedInUserStore.username"
        :key="LoggedInUserStore.updatetrigger"
        :tooltip=false
      />
      <div>
        <q-btn
            icon="edit"
            round
            v-if="editable"
            size="1em"
            color="primary"
            style="right: -4em; top: -2em; z-index: 1"
            @click="show_dialog = true"
        />
      </div>
    </div>
    <q-dialog v-model="show_dialog">
        <q-card>
          <q-card-section class="row items-center">
            <div class="text-h6">Profile Image</div>
            <q-space />
            <q-btn icon="close" flat round dense v-close-popup />
          </q-card-section>

          <q-separator />

          <q-card-section >
            <div class="text-subtitle1 q-mb-md">
              If you are uploading a profile image you and other users will be able to see it.
            </div>
            <div class="row justify-center q-my-md">
              <div class="tw-overflow-visible tw-relative">
                <UserAvatar
                  :size="size"
                  :img="LoggedInUserStore.GetUserAvatarThumbnail(size)"
                  :username="LoggedInUserStore.username"
                  :key="LoggedInUserStore.updatetrigger"
                  :tooltip=false
                />
                <div>
                  <q-btn
                      icon="delete"
                      round
                      size="1em"
                      color="accent"
                      style="right: -4em; top: -2em; z-index: 1"
                      @click="LoggedInUserStore.RemoveUserAvatar()"
                  />
                </div>
              </div>
            </div>
            <div class="row justify-center q-my-md">
              <q-file
                v-model="file"
                label="Change profile image"
                outlined
                style="max-width: 300px"
              >
                <template v-slot:append>
                  <q-icon name="image" />
                </template>
              </q-file>
              <q-btn
                label="Upload"
                color="primary"
                @click="LoggedInUserStore.UploadUserAvatar(file)"
                class="q-mx-md"
              />
            </div>
          </q-card-section>

        </q-card>
      </q-dialog>
</template>

<script lang="ts">
import { useUserStore } from 'stores/user';
import { useLoggedInUserStore } from 'stores/loggedinuser';
import {onMounted, ref} from 'vue';
import { storeToRefs } from 'pinia';
import UserAvatar from 'components/global/UserAvatar.vue';


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
      type: String,
      default: 'md'
    }
  },

  setup(props) {

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

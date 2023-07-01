<template>
    <div class="tw-overflow-visible tw-relative" :class="offset_classes">
      <q-avatar
        color="secondary"
        :size="size_to_width[size]"
        text-color="white"
      >
        <div v-if="LoggedInUserStore.GetUserAvatarThumbnail(size) != ''">
            <img v-bind:src="LoggedInUserStore.GetUserAvatarThumbnail(size)" alt="" class="object-cover">
        </div>
        <div v-else>
          {{ LoggedInUserStore.GetUserUsername.charAt(0).toUpperCase() }}
        </div>
      </q-avatar>
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
                <q-avatar
                  color="secondary"
                  size="100px"
                  text-color="white"
                >
                  <div v-if="LoggedInUserStore.GetUserAvatarThumbnail(size) != ''">
                      <img v-bind:src="LoggedInUserStore.GetUserAvatarThumbnail(size)" alt="" class="object-cover">
                  </div>
                  <div v-else>
                    {{ LoggedInUserStore.GetUserUsername.charAt(0).toUpperCase() }}
                  </div>
                </q-avatar>
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
import { storeToRefs } from 'pinia'


export default {
  name: 'ProfileImageSelf',

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
    const size_to_width = {
      'sm': '30px',
      'md': '50px',
      'lg': '100px',
    }

    const show_dialog = ref(false)
    const LoggedInUserStore = useLoggedInUserStore()
    storeToRefs(LoggedInUserStore)
    const UserStore = useUserStore()
    storeToRefs(UserStore)
    const file = ref<File | null>(null)

    return {
      LoggedInUserStore,
      file,
      size_to_width,
      show_dialog,
    }

  }
}
</script>

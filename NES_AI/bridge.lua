-- Minimal JSON encoder
local function escape_str(s)
    return s:gsub("\\", "\\\\"):gsub('"', '\\"')
end

local function encode_json(tbl)
    local result = {}
    table.insert(result, "{")
    for k, v in pairs(tbl) do
        local key = '"' .. escape_str(k) .. '"'
        local value = ""

        if type(v) == "number" or type(v) == "boolean" then
            value = tostring(v)
        elseif type(v) == "string" then
            value = '"' .. escape_str(v) .. '"'
        else
            value = "null"
        end

        table.insert(result, key .. ":" .. value .. ",")
    end
    if #result > 1 then
        result[#result] = result[#result]:sub(1, -2)
    end
    table.insert(result, "}")
    return table.concat(result)
end

-- Track Q Block hits
local prev_block_states = {}
local function is_q_block(tile)
    return tile == 0x24
end

local function check_q_block_hit()
    local hit = false
    for y = 0, 13 do
        for x = 0, 15 do
            local addr = 0x0500 + y * 16 + x
            local tile = memory.readbyte(addr)
            if is_q_block(tile) and prev_block_states[addr] and prev_block_states[addr] ~= tile then
                hit = true
            end
            prev_block_states[addr] = tile
        end
    end
    return hit
end

local function check_powerup_spawned()
    for i = 0, 63 do
        local sprite = memory.readbyte(0x0200 + i)
        if sprite == 0x24 or sprite == 0x2E then
            return true
        end
    end
    return false
end

-- ⏺️ Track previous lives for detecting life lost
local previous_lives = nil

-- Main memory reader
local function read_game_state()
    local state = {}
    state["timestamp"] = os.time()

    local mode = memory.readbyte(0x0770)
    local mario_state = memory.readbyte(0x000E)
    local x_main = memory.readbyte(0x006D)
    local x_sub = memory.readbyte(0x0086)
    local lives = memory.readbyte(0x075A)
    local power = memory.readbyte(0x0756)

    local x_pos = x_main * 0x100 + x_sub
    state["mario_x"] = x_pos
    state["mario_y"] = memory.readbyte(0x00CE)

    if power == 0 then
        state["powerup"] = "small"
    elseif power == 1 then
        state["powerup"] = "big"
    elseif power == 2 then
        state["powerup"] = "fire"
    else
        state["powerup"] = "unknown"
    end

    local display_lives = lives + 1
    state["lives"] = display_lives
    state["coins"] = memory.readbyte(0x075E)
    state["flagpole"] = memory.readbyte(0x00FC) == 3
    state["mario_dead"] = mario_state == 0x06

    -- ✅ Life lost tracking
    if previous_lives ~= nil and display_lives < previous_lives then
        state["life_lost"] = true
    else
        state["life_lost"] = false
    end
    previous_lives = display_lives

    -- Game status classification (improved)
    if mode == 0x03 and lives == 255 then
        state["game_status"] = "game_over"
    elseif mode == 0x00 then
        state["game_status"] = "title"
    elseif mode == 0x01 then
        if mario_state == 0x08 then
            state["game_status"] = "playing"
        elseif mario_state == 0x06 or lives == 0 then
            state["game_status"] = "dying"
        else
            state["game_status"] = "transition"
        end
    elseif mario_state == 0x07 then
        state["game_status"] = "lives_screen"
    else
        state["game_status"] = "unknown"
    end

    state["enemy_killed"] = memory.readbyte(0x07DD) ~= 0
    state["q_block_hit"] = check_q_block_hit()
    state["q_block_powerup"] = check_powerup_spawned()

    -- Debug fields
    state["_mode"] = mode
    state["_mario_state"] = mario_state

    return state
end

-- Write JSON
local function write_to_json(state)
    local file = io.open("mario_memory.json", "w")
    if file then
        file:write(encode_json(state))
        file:close()
    end
end

-- Debug log to file
local function write_debug_log(state)
    local f = io.open("memory_debug.log", "a")
    if f then
        f:write(string.format(
            "mode:%02X lives:%d death:%02X x:%d.%d power:%d stomp:%02X status:%s life_lost:%s\n",
            state["_mode"],
            memory.readbyte(0x075A),
            state["_mario_state"],
            memory.readbyte(0x006D),
            memory.readbyte(0x0086),
            memory.readbyte(0x0756),
            memory.readbyte(0x07DD),
            state["game_status"],
            tostring(state["life_lost"])
        ))
        f:close()
    end
end

-- Print to terminal
local function print_debug_terminal(state)
    print(string.format(
        "[MEM] mode:%02X | mario_state:%02X | x:%d | y:%d | lives:%d | status:%s | life_lost:%s",
        state["_mode"],
        state["_mario_state"],
        state["mario_x"],
        state["mario_y"],
        state["lives"],
        state["game_status"],
        tostring(state["life_lost"])
    ))
end

-- Main loop
while true do
    local game_state = read_game_state()
    write_to_json(game_state)
    write_debug_log(game_state)
    print_debug_terminal(game_state)
    emu.frameadvance()
end

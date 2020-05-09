camera_x = 0
camera_y = 0

function make_object(x, y, size, color)
	return {x=x, y=y, size=size, color=color}
end

objects = {
	make_object(0, 0, 0.1),
	make_object(0, 0.25, 0.02),
	make_object(0, 0.5, 0.02),
	make_object(0, 0.75, 0.02),
	make_object(0, 1, 0.02),
	make_object(0, 1.25, 0.02),
	make_object(10, 20, 0.05)
}


function to_polar(x, y)
	local distance = math.sqrt(x*x + y*y)
	local angle = math.atan2(y, x)
	return angle, distance
end

function from_polar(angle, distance)
	local x = math.cos(angle) * distance
	local y = math.sin(angle) * distance
	return x, y
end


function squash_distance(distance, size, sharpness)
	
	distance = distance * 2.5
	local result_distance = distance
	local result_size = size
	if distance > sharpness
	then
		result_distance = math.atan((distance - sharpness) / (1 - sharpness)) * (1 - sharpness) + sharpness
		result_size = size * result_distance / distance
	end
	result_distance = result_distance / 2.5
	return result_distance, result_size;
end



function transform(x, y, size)
	x = x - camera_x
	y = y - camera_y
	local angle, distance = to_polar(x, y)
	distance, size = squash_distance(distance, size, 0.5)
	x, y = from_polar(angle, distance)
	return x, y, size
end


function screen_transform(x, y, size)
	local window_scale = love.graphics.getHeight()
	x = x * window_scale
	y = y * window_scale
	size = size * window_scale
	x = x + love.graphics.getWidth() / 2
	y = y + love.graphics.getHeight() / 2

	return x, y, size
end



function love.draw()
	for i, object in ipairs(objects)
	do
		love.graphics.circle("fill", screen_transform(transform(object.x, object.y, object.size)))
	end
end

camera_speed = 0.02

function love.update()

	if love.keyboard.isDown("left")
	then
		camera_x = camera_x - camera_speed
	end
	if love.keyboard.isDown("right")
	then
		camera_x = camera_x + camera_speed
	end
	if love.keyboard.isDown("up")
	then
		camera_y = camera_y - camera_speed
	end
	if love.keyboard.isDown("down")
	then
		camera_y = camera_y + camera_speed
	end
end
